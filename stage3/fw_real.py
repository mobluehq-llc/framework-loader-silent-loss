"""S3/M4 on real files: framework default loaders; writes token multisets to realworld/work/fw/. Run with .venv_frameworks.
usage: python -I stage3/fw_real.py [--docling]  (without the flag: LangChain + LlamaIndex only; with it: Docling only)"""
import sys, os, csv, json, signal, collections, re, time, warnings, hashlib
warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); H = os.path.join(ROOT, "realworld"); sys.path.insert(0, HERE)
import fw_load
TOK = re.compile(r"[a-z0-9é’]+")
MAP = {"pdf": ["lc_pdf", "li_pdf"], "html": ["lc_html", "li_html"], "txt": ["li_txt"]}
if "--docling" in sys.argv: MAP = {"pdf": ["docling_pdf"], "html": ["docling_html"], "txt": []}
OUT = os.path.join(H, "work", "fw"); os.makedirs(OUT, exist_ok=True)
files = []
for tsv in ("MANIFEST_fetch.tsv", "MANIFEST_gov.tsv"):
    for r in csv.DictReader(open(os.path.join(H, tsv)), delimiter="\t"):
        k = r["kind"]; gov = tsv.endswith("gov.tsv"); path = os.path.join(H, "raw", "gov", k, r["file"]) if gov else os.path.join(H, "raw", k, r["file"])
        files.append((path, {"arxiv": "pdf", "wiki": "html"}.get(k, k), r["sha256"]))
def tmo(*a): raise TimeoutError("timeout")
signal.signal(signal.SIGALRM, tmo)
for p, fmt, sha in files:
    for fid in MAP[fmt]:
        out = os.path.join(OUT, "%s_%s.json" % (sha[:16], fid))
        if os.path.exists(out): continue
        t = time.time(); signal.alarm(150)
        try: pages = fw_load.load(fid, p); rec = dict(raised=False, tokens=dict(collections.Counter(TOK.findall("\n".join(pages).lower()))), npages=len(pages))
        except BaseException as e: rec = dict(raised=True, exc=type(e).__name__ + ": " + str(e)[:100])
        signal.alarm(0); rec.update(path=p, fmt=fmt, loader=fid, secs=round(time.time() - t, 1)); json.dump(rec, open(out, "w")); print(os.path.basename(p), fid, "raised" if rec["raised"] else "ok", rec["secs"], flush=True)
