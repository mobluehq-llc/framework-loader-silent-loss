"""AMENDMENT 5 (PLAN.md): P04 only, corrected generator (stage2/gen2_p4fix.py). usage: <venv>/bin/python -I stage3/p4fix_run.py FIXDIR OUT.json LOADER[,LOADER...]
Loaders: lc_pdf li_pdf docling_pdf (venv_frameworks) | hs_pdf un_pdf mk_pdf (venv_frameworks2) | pymupdf (library venv). Metric as fw_run.py (run3.metrics)."""
import sys, os, json, glob, warnings
warnings.simplefilter("ignore"); HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import loaders3 as L
L.DOCGRAIN.update({"docling_pdf", "hs_pdf", "un_pdf", "mk_pdf"})  # whole-document grain, as in fw_run.py and fw2_run.py
import run3
_dc = None
def load(fid, p):
    global _dc
    if fid == "lc_pdf":
        from langchain_community.document_loaders import PyPDFLoader; return [d.page_content for d in PyPDFLoader(p).load()]
    if fid == "li_pdf":
        from llama_index.core import SimpleDirectoryReader; return [x.text for x in SimpleDirectoryReader(input_files=[p]).load_data()]
    if fid == "docling_pdf":
        if _dc is None:
            from docling.document_converter import DocumentConverter; _dc = DocumentConverter()
        return [_dc.convert(p).document.export_to_text()]
    if fid == "hs_pdf":
        from haystack.components.converters import PyPDFToDocument; return [d.content or "" for d in PyPDFToDocument().run(sources=[p])["documents"]]
    if fid == "un_pdf":
        from unstructured.partition.auto import partition; return ["\n".join(e.text for e in partition(filename=p, content_type="application/pdf"))]
    if fid == "mk_pdf":
        from markitdown import MarkItDown; return [MarkItDown().convert(p).text_content]
    if fid == "pymupdf":
        import pymupdf; return [pg.get_text() for pg in pymupdf.open(p)]
    raise KeyError(fid)
recs = []
for fid in sys.argv[3].split(","):
    for sd in sorted(glob.glob(os.path.join(sys.argv[1], "*")))[: (5 if fid == "docling_pdf" else 20)]:
        p = os.path.join(sd, "P04_rotated.pdf"); man = json.load(open(p + ".json")); rec = dict(seed=os.path.basename(sd), fixture=man["id"], loader=fid)
        try: pages = load(fid, p); rec["raised"] = False
        except BaseException as e: pages = None; rec.update(raised=True, exc=type(e).__name__)
        if pages is not None:
            m = run3.metrics(man, fid if fid != "pymupdf" else "lc_pdf", dict(pages=pages)); rec["recall_core"] = (sum(v["found"] for k, v in m["by_kind"].items() if k in run3.CORE), sum(v["total"] for k, v in m["by_kind"].items() if k in run3.CORE))
        recs.append(rec); print(fid, rec["seed"], rec.get("recall_core"), flush=True)
json.dump(recs, open(sys.argv[2], "w"))
