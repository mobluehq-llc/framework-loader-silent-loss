"""Stage-2 loaders (naive documented idioms). load(lid, path) -> list[str]. Stage-1 loaders are re-used."""
import os, sys, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import loaders as L1
FAMILY = dict(L1.FAMILY)
FAMILY.update(pdftotext="poppler", pymupdf4llm="pymupdf", markitdown_pdf="markitdown", docx2txt="docx2txt", mammoth="mammoth",
              pptx_shapes="python-pptx", pptx_walk="python-pptx", markitdown_pptx="markitdown",
              bs4_text="bs4", bs4_sep="bs4", lxml_text="lxml", trafilatura="trafilatura", html2text="html2text")
IDS = dict(pdf=L1.PDF + ["pdftotext", "pymupdf4llm", "markitdown_pdf"], docx=L1.DOCX + ["docx2txt", "mammoth"],
           pptx=["pptx_shapes", "pptx_walk", "markitdown_pptx"], html=["bs4_text", "bs4_sep", "lxml_text", "trafilatura", "html2text"], txt=L1.TXT)
DOCGRAIN = {"markitdown_pdf"}

def _walk(shapes):
    out = []
    for sh in shapes:
        if sh.shape_type == 6: out += _walk(sh.shapes)          # group
        if sh.has_text_frame: out.append(sh.text_frame.text)
        if getattr(sh, "has_table", False) and sh.has_table:
            for row in sh.table.rows:
                for c in row.cells: out.append(c.text)
    return out

def _read(p):
    with open(p, encoding="utf-8") as f: return f.read()

def load(lid, p):
    if lid == "pdftotext":
        s = subprocess.run(["pdftotext", p, "-"], capture_output=False, stdout=subprocess.PIPE, check=True).stdout.decode("utf8", "replace")
        parts = s.split("\f"); return parts[:-1] if parts and parts[-1] == "" else parts
    if lid == "pymupdf4llm":
        import pymupdf4llm; return [c["text"] for c in pymupdf4llm.to_markdown(p, page_chunks=True, show_progress=False)]
    if lid in ("markitdown_pdf", "markitdown_pptx"):
        from markitdown import MarkItDown; return [MarkItDown().convert(p).text_content]
    if lid == "docx2txt":
        import docx2txt; return [docx2txt.process(p)]
    if lid == "mammoth":
        import mammoth
        with open(p, "rb") as f: return [mammoth.extract_raw_text(f).value]
    if lid == "pptx_shapes":
        import pptx; return [" ".join(sh.text_frame.text for sh in s.shapes if sh.has_text_frame) for s in pptx.Presentation(p).slides]
    if lid == "pptx_walk":
        import pptx; out = []
        for s in pptx.Presentation(p).slides:
            t = _walk(s.shapes)
            if s.has_notes_slide: t.append(s.notes_slide.notes_text_frame.text)
            out.append(" ".join(t))
        return out
    if lid == "bs4_text":
        from bs4 import BeautifulSoup; return [BeautifulSoup(_read(p), "html.parser").get_text()]
    if lid == "bs4_sep":
        from bs4 import BeautifulSoup; return [BeautifulSoup(_read(p), "html.parser").get_text(" ")]
    if lid == "lxml_text":
        import lxml.html; return [lxml.html.fromstring(_read(p)).text_content()]
    if lid == "trafilatura":
        import trafilatura; return [trafilatura.extract(_read(p)) or ""]
    if lid == "html2text":
        import html2text; return [html2text.html2text(_read(p))]
    return L1.load(lid, p)
