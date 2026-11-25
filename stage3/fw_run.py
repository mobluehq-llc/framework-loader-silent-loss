"""S3/M4: framework default loaders on the S2 synthetic seeds. Run with .venv_frameworks. usage: python -I stage3/fw_run.py FIXDIR OUT.json
Silent core loss as in the grid (token recall < 1 on a core kind) with no exception; framework stderr is not scored."""
import sys, os, json, glob, signal, warnings, time, collections
warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import loaders3 as L
L.DOCGRAIN.update({"docling_pdf", "docling_docx", "docling_pptx", "docling_html", "li_docx", "li_html", "li_txt", "li_pptx", "lc_html", "lc_docx"})
import run3
CORE = run3.CORE; UNREAD = run3.UNREAD
_dc = None
def load(fid, p):
    global _dc
    if fid == "lc_html":
        from langchain_community.document_loaders import BSHTMLLoader; return [d.page_content for d in BSHTMLLoader(p).load()]
    if fid == "lc_pdf":
        from langchain_community.document_loaders import PyPDFLoader; return [d.page_content for d in PyPDFLoader(p).load()]
    if fid == "lc_docx":
        from langchain_community.document_loaders import Docx2txtLoader; return [d.page_content for d in Docx2txtLoader(p).load()]
    if fid.startswith("li_"):
        from llama_index.core import SimpleDirectoryReader; d = SimpleDirectoryReader(input_files=[p]).load_data(); r = [x.text for x in d]
        return r if fid == "li_pdf" else ["\n".join(r)]
    if fid.startswith("docling_"):
        if _dc is None:
            from docling.document_converter import DocumentConverter; _dc = DocumentConverter()
        return [_dc.convert(p).document.export_to_text()]
    raise KeyError(fid)
MAP = {"pdf": ["lc_pdf", "li_pdf", "docling_pdf"], "docx": ["lc_docx", "li_docx", "docling_docx"], "pptx": ["li_pptx", "docling_pptx"], "html": ["lc_html", "li_html", "docling_html"], "txt": ["li_txt"]}
def tmo(*a): raise TimeoutError("timeout")
signal.signal(signal.SIGALRM, tmo)
recs = []; skip = set(sys.argv[3].split(",")) if len(sys.argv) > 3 else set()
for sd in sorted(glob.glob(os.path.join(sys.argv[1], "*"))):
    for mp in sorted(glob.glob(os.path.join(sd, "*.json"))):
        man = json.load(open(mp)); path = mp[:-5]; fmt = man["format"]
        for fid in MAP[fmt]:
            if fid in skip: continue
            rec = dict(seed=os.path.basename(sd), fixture=man["id"], fmt=fmt, loader=fid); t = time.time()
            signal.alarm(300)
            try: pages = load(fid, path); rec["raised"] = False; rec["exc"] = None
            except BaseException as e: pages = None; rec.update(raised=True, exc=type(e).__name__ + ": " + str(e)[:120])
            signal.alarm(0); rec["secs"] = round(time.time() - t, 1)
            if pages is not None:
                m = run3.metrics(man, fid, dict(pages=pages)); rec.update(m)
                g = lambda ks: any(v["found"] < v["total"] for k, v in m["by_kind"].items() if k in ks)
                rec["loss_core"] = g(CORE) or m["page_count_error"] != 0 or m["misnumbered"] > 0; rec["loss_unread"] = g(UNREAD)
                rec["recall_core"] = (sum(v["found"] for k, v in m["by_kind"].items() if k in CORE), sum(v["total"] for k, v in m["by_kind"].items() if k in CORE))
            recs.append(rec); print(rec["seed"], rec["fixture"], fid, "raised" if rec["raised"] else ("LOSS" if rec["loss_core"] else "ok"), rec["secs"], flush=True)
        json.dump(recs, open(sys.argv[2], "w"))
