"""S1 + S3/M3 synthetic part: both-miss classes and gen2 PDF classes under W, W2 (ink branch), W-dual (pypdfium2 U pymupdf union reference).
usage: python -I stage3/run_bm.py FIXDIR OUT.json   (FIXDIR/<seed>/bm/*.pdf and FIXDIR/<seed>/P*.pdf; gen_bothmiss output under <seed>/bm)"""
import sys, os, json, glob, collections, re
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE); sys.path.insert(0, os.path.join(HERE, "..", "stage2")); sys.path.insert(0, os.path.join(HERE, ".."))
import loaders2 as L
from conserve2 import account, ConservationError, toks, recall
import inkflags, pymupdf, pypdfium2, pikepdf
def engine_toks(path):
    d = pypdfium2.PdfDocument(path); a = [toks(d[i].get_textpage().get_text_range()) for i in range(len(d))]; d.close()
    m = pymupdf.open(path); b = [toks(pg.get_text()) for pg in m]; m.close(); return a, b
def union(a, b):
    c = collections.Counter(a); 
    for k, v in b.items(): c[k] = max(c[k], v)
    return c
def wdual(path, pages):
    raw = open(path, "rb").read()
    if raw.rstrip()[-5:] != b"%%EOF": raise ConservationError("file truncated")
    try: a, b = engine_toks(path)
    except Exception as e: raise ConservationError("engine raised %s" % type(e).__name__)
    pdf = pikepdf.open(path)
    if pdf.check_pdf_syntax(): raise ConservationError("structure problems")
    if not (len(a) == len(b) == len(pages)): raise ConservationError("page count disagree")
    fl = inkflags.page_flags(path); st = []
    for i, t in enumerate(pages):
        R = union(a[i], b[i])
        if R: st.append("read" if recall(R, toks(t)) == 1.0 else (_ for _ in ()).throw(ConservationError("page recall < 1")))
        else: st.append("declared_unreadable" if (fl[i]["unreadable_ink"] or pdf.pages[i].obj.get("/Annots") is not None) else "declared_empty")
    return st
def main():
    fix, out = sys.argv[1], sys.argv[2]; recs = []
    for sd in sorted(glob.glob(os.path.join(fix, "*"))):
        seed = os.path.basename(sd); files = sorted(glob.glob(os.path.join(sd, "P*.pdf"))) + sorted(glob.glob(os.path.join(sd, "bm", "*.pdf")))
        for p in files:
            man = json.load(open(p + ".json")); cid = man["id"]
            truth = [(u["A"] + u["B"]) if "A" in u else u["words"] for u in man["units"]]
            tc = [collections.Counter(t for w in ws for t in toks(w)) for ws in truth]
            for lid in L.IDS["pdf"]:
                if lid == "markitdown_pdf": continue  # document-grain output: no per-page truth alignment; reported separately in the S3 real-file part
                try: pages = L.load(lid, p); raised = None
                except BaseException as e: pages = None; raised = type(e).__name__
                rec = dict(seed=seed, cls=cid, loader=lid, raised=raised, npages=len(tc))
                if raised: recs.append(rec); continue
                inc = [bool(tc[i]) and (i >= len(pages) or recall(tc[i], toks(pages[i])) < 1.0) for i in range(len(tc))]
                rec["incomplete_pages"] = sum(inc); rec["truth_pages"] = sum(1 for t in tc if t); rec["pages_out"] = len(pages)
                cell = dict(raised=False, pages=pages)
                for wname in ("W", "W2", "Wdual"):
                    try:
                        if wname == "Wdual": st = wdual(p, pages)
                        else:
                            st = account(p, "pdf", lid, cell, None, L.DOCGRAIN)["units"]
                            if wname == "W2":
                                fl = inkflags.page_flags(p); st = [("declared_unreadable" if (i < len(fl) and fl[i]["unreadable_ink"] and s in ("read", "declared_empty")) else s) for i, s in enumerate(st)]
                    except ConservationError as e: rec[wname] = dict(refused=str(e)[:60]); continue
                    except Exception as e: rec[wname] = dict(fault="%s: %s" % (type(e).__name__, e)); continue
                    silent = sum(1 for i, s in enumerate(st) if i < len(inc) and inc[i] and s in ("read", "declared_empty"))
                    decl_unread = sum(1 for s in st if s == "declared_unreadable")
                    rec[wname] = dict(silent=silent, declared_unreadable=decl_unread, declared_empty_when_truth_nonempty=sum(1 for i, s in enumerate(st) if i < len(tc) and s == "declared_empty" and tc[i]), declared_unreadable_when_truth_empty=sum(1 for i, s in enumerate(st) if i < len(tc) and s == "declared_unreadable" and not tc[i]))
                recs.append(rec)
    json.dump(recs, open(out, "w"), indent=0); print(len(recs), "runs")
main()
