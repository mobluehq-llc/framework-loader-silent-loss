"""Naive documented idioms. load(loader_id, path) -> list[str] (one string per page/unit)."""
FAMILY = {"pypdf": "pypdf", "pypdf2": "pypdf", "pdfminer_pages": "pdfminer", "pdfminer_high": "pdfminer",
          "pdfplumber": "pdfplumber", "pymupdf": "pymupdf", "pypdfium2": "pdfium",
          "docx_paragraphs": "python-docx", "docx_full": "python-docx",
          "txt_utf8_strict": "stdlib", "txt_utf8_ignore": "stdlib", "txt_utf8_replace": "stdlib", "txt_latin1": "stdlib",
          "txt_charset_normalizer": "charset-normalizer", "stub_empty": "stub"}
PDF = ["pypdf", "pypdf2", "pdfminer_pages", "pdfminer_high", "pdfplumber", "pymupdf", "pypdfium2"]
DOCX = ["docx_paragraphs", "docx_full"]
TXT = ["txt_utf8_strict", "txt_utf8_ignore", "txt_utf8_replace", "txt_latin1", "txt_charset_normalizer"]

def _tables(tbls):
    out = []
    for t in tbls:
        for row in t.rows:
            for cell in row.cells:
                out += [p.text for p in cell.paragraphs]; out += _tables(cell.tables)
    return out

def _rd(p, **kw):
    with open(p, **kw) as f: return f.read()

def load(lid, p):
    if lid == "stub_empty": return [""] * 10
    if lid == "pypdf":
        import pypdf; return [pg.extract_text() for pg in pypdf.PdfReader(p).pages]
    if lid == "pypdf2":
        import PyPDF2; return [pg.extract_text() for pg in PyPDF2.PdfReader(p).pages]
    if lid == "pdfminer_pages":
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer
        return ["\n".join(e.get_text() for e in pg if isinstance(e, LTTextContainer)) for pg in extract_pages(p)]
    if lid == "pdfminer_high":
        from pdfminer.high_level import extract_text
        s = extract_text(p); parts = s.split("\f")
        if parts and parts[-1] == "": parts = parts[:-1]
        return parts
    if lid == "pdfplumber":
        import pdfplumber
        with pdfplumber.open(p) as pdf: return [(pg.extract_text() or "") for pg in pdf.pages]
    if lid == "pymupdf":
        import pymupdf
        with pymupdf.open(p) as d: return [pg.get_text() for pg in d]
    if lid == "pypdfium2":
        import pypdfium2 as pdfium
        d = pdfium.PdfDocument(p); r = [d[i].get_textpage().get_text_range() for i in range(len(d))]; d.close(); return r
    if lid == "docx_paragraphs":
        import docx; return ["\n".join(x.text for x in docx.Document(p).paragraphs)]
    if lid == "docx_full":
        import docx; d = docx.Document(p); out = [x.text for x in d.paragraphs] + _tables(d.tables)
        for s in d.sections:
            out += [x.text for x in s.header.paragraphs] + [x.text for x in s.footer.paragraphs]
        return ["\n".join(out)]
    if lid == "txt_utf8_strict": return [_rd(p, encoding="utf-8")]
    if lid == "txt_utf8_ignore": return [_rd(p, encoding="utf-8", errors="ignore")]
    if lid == "txt_utf8_replace": return [_rd(p, encoding="utf-8", errors="replace")]
    if lid == "txt_latin1": return [_rd(p, encoding="latin-1")]
    if lid == "txt_charset_normalizer":
        from charset_normalizer import from_path
        b = from_path(p).best(); return [str(b) if b is not None else ""]
    raise KeyError(lid)
