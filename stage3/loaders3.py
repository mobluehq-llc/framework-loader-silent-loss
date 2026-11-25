"""S2 competent-baseline pipelines (PREREG_REDTEAM.md S2). Frozen before the S2 run. load(lid, path) -> list[str]."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import loaders2_frozen as L2
FAMILY = dict(L2.FAMILY); FAMILY.update(comp_pdf_A="pymupdf+repairflag", comp_pdf_B="pdfium+qpdfcheck", txt_strict_bom="stdlib")
IDS = dict(pdf=["comp_pdf_A", "comp_pdf_B"], docx=["docx_full"], pptx=["pptx_walk"], html=["bs4_sep"], txt=["txt_strict_bom"])
DOCGRAIN = set()
def load(lid, p):
    if lid == "comp_pdf_A":
        import pymupdf
        pymupdf.TOOLS.reset_mupdf_warnings()
        with pymupdf.open(p) as d:
            out = [pg.get_text() for pg in d]; rep = d.is_repaired
        w = pymupdf.TOOLS.mupdf_warnings()
        if rep or (w and w.strip()): raise RuntimeError("PyMuPDF: document repaired or MuPDF warnings: %s" % (w or "")[:80].replace("\n", " | "))
        return out
    if lid == "comp_pdf_B":
        import pikepdf, pypdfium2 as pdfium
        raw = open(p, "rb").read()
        if raw.rstrip()[-5:] != b"%%EOF": raise RuntimeError("no %%EOF")
        pdf = pikepdf.open(p); probs = pdf.check_pdf_syntax()
        if probs: raise RuntimeError("qpdf-style check: %s" % probs[0][:80])
        d = pdfium.PdfDocument(p); r = [d[i].get_textpage().get_text_range() for i in range(len(d))]; d.close(); return r
    if lid == "txt_strict_bom":
        b = open(p, "rb").read()
        return [b.decode("utf-16") if b[:2] in (b"\xff\xfe", b"\xfe\xff") else b.decode("utf-8")]
    return L2.load(lid, p)
