"""AG v16 (ChatGPT R2 blocker 2): Unstructured FILENAME-ONLY call, partition(filename=path), no content_type; otherwise identical to fw2_run.py (same scoring and fixtures), restricted to the un_* rows. AG_UN_MIME=1 restores the explicit content_type call of fw2_run.py, so both calls can be run in one environment as a parity control. Original docstring follows.
SAG2 pick 1: Haystack, Unstructured, MarkItDown default loaders on the S3 framework seeds (20261401-20261420).
Run with .venv_frameworks2. usage: python -I stage3/fw2_run.py FIXDIR OUT.json
Scoring identical to stage3/fw_run.py (multiset token recall by kind, whole-document grain, raised = exception)."""
import sys, os, json, glob, signal, warnings, time
warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import loaders3 as L
ALL = {"hs_pdf","hs_docx","hs_html","hs_txt","un_pdf","un_docx","un_pptx","un_html","un_txt","mk_pdf","mk_docx","mk_pptx","mk_html","mk_txt"}
L.DOCGRAIN.update(ALL)
import run3
CORE = run3.CORE; UNREAD = run3.UNREAD

def load(fid, p):
    fw, fmt = fid.split("_")
    if fw == "hs":
        from haystack.components.converters import PyPDFToDocument, DOCXToDocument, HTMLToDocument, TextFileToDocument
        c = dict(pdf=PyPDFToDocument, docx=DOCXToDocument, html=HTMLToDocument, txt=TextFileToDocument)[fmt]()
        return [d.content or "" for d in c.run(sources=[p])["documents"]]
    if fw == "un":
        from unstructured.partition.auto import partition
        MIME = dict(pdf="application/pdf", docx="application/vnd.openxmlformats-officedocument.wordprocessingml.document", pptx="application/vnd.openxmlformats-officedocument.presentationml.presentation", html="text/html", txt="text/plain")
        els = partition(filename=p, content_type=MIME[fmt]) if os.environ.get("AG_UN_MIME") == "1" else partition(filename=p)
        return ["\n".join(e.text for e in els)]
    if fw == "mk":
        from markitdown import MarkItDown
        return [MarkItDown().convert(p).text_content]
    raise KeyError(fid)

MAP = {f: ["un_" + f] for f in ("pdf", "docx", "pptx", "html", "txt")}
def tmo(*a): raise TimeoutError("timeout")
signal.signal(signal.SIGALRM, tmo)
class _H(__import__("logging").Handler):
    def __init__(s): super().__init__(30); s.n = 0
    def emit(s, r): s.n += 1
if __name__ == "__main__":
    import logging; H = _H(); logging.getLogger().addHandler(H); logging.getLogger().setLevel(30)
    recs = []
    for sd in sorted(glob.glob(os.path.join(sys.argv[1], "*"))):
        for mp in sorted(glob.glob(os.path.join(sd, "*.json"))):
            man = json.load(open(mp)); path = mp[:-5]; fmt = man["format"]
            for fid in MAP[fmt]:
                rec = dict(seed=os.path.basename(sd), fixture=man["id"], fmt=fmt, loader=fid); t = time.time()
                signal.alarm(300); H.n = 0
                try: pages = load(fid, path); rec["raised"] = False; rec["exc"] = None
                except BaseException as e: pages = None; rec.update(raised=True, exc=type(e).__name__ + ": " + str(e)[:160])
                signal.alarm(0); rec["secs"] = round(time.time() - t, 1); rec["logged_warnings"] = H.n  # descriptive only; not part of LOUD (same as fw_run.py)
                if pages is not None:
                    m = run3.metrics(man, fid, dict(pages=pages)); rec.update(m)
                    g = lambda ks: any(v["found"] < v["total"] for k, v in m["by_kind"].items() if k in ks)
                    rec["loss_core"] = g(CORE); rec["loss_unread"] = g(UNREAD)
                    rec["recall_core"] = (sum(v["found"] for k, v in m["by_kind"].items() if k in CORE), sum(v["total"] for k, v in m["by_kind"].items() if k in CORE))
                    rec["recall_by_kind"] = {k: round(v["found"] / v["total"], 4) for k, v in m["by_kind"].items() if v["total"]}
                recs.append(rec); print(rec["seed"], rec["fixture"], fid, "raised" if rec["raised"] else ("LOSS" if rec["loss_core"] else "ok"), rec.get("exc") or "", rec["secs"], flush=True)
            json.dump(recs, open(sys.argv[2], "w"))
