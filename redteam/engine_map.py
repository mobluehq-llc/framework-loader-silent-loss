"""(f) Map shared engines from installed package metadata. usage: .venv/bin/python -I redteam/engine_map.py"""
import importlib.metadata as m, re
PK = ["pypdf", "PyPDF2", "pdfminer.six", "pdfplumber", "PyMuPDF", "pymupdf4llm", "pypdfium2", "markitdown", "python-docx", "docx2txt", "mammoth", "python-pptx", "beautifulsoup4", "lxml", "trafilatura", "html2text", "charset-normalizer"]
for p in PK:
    req = [re.split(r"[ ;<>=!~\[(]", r)[0] for r in (m.requires(p) or []) if "extra ==" not in r]
    print("%-18s %-8s requires: %s" % (p, m.version(p), ", ".join(req)))
