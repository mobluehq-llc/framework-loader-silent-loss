"""(b) PyMuPDF Document.is_repaired + warning buffer on P11 (truncated) files; per-page ids/recall; qpdf --check, pikepdf. usage: .venv/bin/python -I redteam/p11_repair.py FIXDIR"""
import sys, glob, json, os, subprocess, collections, re
import pymupdf, pymupdf4llm, pypdfium2
fx = sys.argv[1]; rows = []
TOK = re.compile(r"[a-z0-9é’]+")
def toks(s): return collections.Counter(TOK.findall(s.lower()))
for sd in sorted(glob.glob(os.path.join(fx, "*"))):
    for mp in sorted(glob.glob(os.path.join(sd, "P11*.json"))):
        man = json.load(open(mp)); p = mp[:-5]
        pymupdf.TOOLS.reset_mupdf_warnings()
        d = pymupdf.open(p); rep = d.is_repaired; n = len(d); texts = [pg.get_text() for pg in d]; w = pymupdf.TOOLS.mupdf_warnings(); d.close()
        # warning buffer is also read AFTER the idiom has run: it is a separate call the idiom never makes
        rec = []
        for i, u in enumerate(man["units"]):
            if not u["words"]: rec.append(None); continue
            R = collections.Counter(); [R.update(toks(x)) for x in u["words"]]
            O = toks(texts[i]) if i < len(texts) else collections.Counter(); rec.append(sum(min(v, O[k]) for k, v in R.items()) / sum(R.values()))
        q = subprocess.run(["qpdf", "--check", p], capture_output=True, text=True) if subprocess.call(["which", "qpdf"], stdout=subprocess.DEVNULL) == 0 else None
        try:
            pdfium_err = None; pf = pypdfium2.PdfDocument(p); pf.close()
        except Exception as e: pdfium_err = type(e).__name__
        rows.append(dict(seed=os.path.basename(sd), is_repaired=rep, mupdf_warning_len=len(w or ""), warn_head=(w or "")[:80].replace("\n", " | "),
            pages_truth=man["page_count"], pages_returned=n, page_recall=[None if r is None else round(r, 2) for r in rec],
            qpdf_rc=None if q is None else q.returncode, pypdfium2_raises=pdfium_err))
print("P11 files", len(rows))
print("is_repaired True:", sum(r["is_repaired"] for r in rows), " warning buffer nonempty:", sum(r["mupdf_warning_len"] > 0 for r in rows), " page count == truth:", sum(r["pages_truth"] == r["pages_returned"] for r in rows))
print("qpdf available:", rows[0]["qpdf_rc"] is not None, "qpdf rc!=0 (check fails):", sum(1 for r in rows if r["qpdf_rc"]), " pypdfium2 raises:", sum(1 for r in rows if r["pypdfium2_raises"]))
print("warning heads:", collections.Counter(r["warn_head"] for r in rows).most_common(3))
print("example:", rows[0])
sil = [sum(1 for x in r["page_recall"] if x is not None and x < 1) for r in rows]; print("pages with recall<1 per file: min/max", min(sil), max(sil), "; pages with recall 0:", sum(sum(1 for x in r["page_recall"] if x == 0) for r in rows))
json.dump(rows, open(sys.argv[2], "w")) if len(sys.argv) > 2 else None
