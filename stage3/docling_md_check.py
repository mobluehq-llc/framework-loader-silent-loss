"""Post-hoc (not registered): Docling export_to_markdown on D03, S04, P04, seeds 20261401-05, same metric as fw_run.py.
usage: .venv_frameworks/bin/python -I stage3/docling_md_check.py > results/docling_markdown_check.txt"""
import sys, os, json, glob, warnings
warnings.simplefilter("ignore")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import loaders3 as L
L.DOCGRAIN.update({"docling_pdf", "docling_docx", "docling_pptx"})
import run3
from docling.document_converter import DocumentConverter
dc = DocumentConverter(); ROOT = os.path.join(os.path.dirname(HERE), "fixtures3_fw")
tot = {}
for sd in sorted(os.listdir(ROOT))[:5]:
    for fx, fid in (("D03_header_footer.docx", "docling_docx"), ("S04_notes.pptx", "docling_pptx"), ("P04_rotated.pdf", "docling_pdf")):
        p = os.path.join(ROOT, sd, fx); man = json.load(open(p + ".json"))
        for mode in ("text", "markdown"):
            d = dc.convert(p).document; out = d.export_to_text() if mode == "text" else d.export_to_markdown()
            m = run3.metrics(man, fid, dict(pages=[out])); f = sum(v["found"] for k, v in m["by_kind"].items() if k in run3.CORE); t = sum(v["total"] for k, v in m["by_kind"].items() if k in run3.CORE)
            a = tot.setdefault((fx, mode), [0, 0]); a[0] += f; a[1] += t
for (fx, mode), (f, t) in sorted(tot.items()): print("%-24s %-9s seeds 5 pooled core recall %.2f (%d of %d)" % (fx, mode, f / t, f, t))
