"""Conservation wrapper: account for every unit; classify using an independent reader (pikepdf / raw zip XML / byte decode)."""
import re, zipfile, io
class ConservationError(Exception): pass

def _pdf_accountant(path):
    import pikepdf
    raw = open(path, "rb").read()
    if raw.rstrip()[-5:] != b"%%EOF": raise ConservationError("file truncated: no %%EOF")
    try: pdf = pikepdf.open(path)
    except pikepdf.PasswordError: raise ConservationError("password required")
    except Exception as e: raise ConservationError("unopenable: %s" % type(e).__name__)
    if pdf.check_pdf_syntax(): raise ConservationError("structure problems: repair needed")
    kinds = []
    for pg in pdf.pages:
        try:
            cs = pg.obj.get("/Contents"); data = b""
            if cs is not None:
                data = b"".join(s.read_bytes() for s in cs) if isinstance(cs, pikepdf.Array) else cs.read_bytes()
        except Exception: data = b"?"
        has_text = bool(re.search(rb"\bT[jJ]\b|'|\"", data)) and b"BT" in data
        res = pg.obj.get("/Resources"); xo = res.get("/XObject") if res is not None else None
        has_img = xo is not None and len(xo.keys()) > 0
        has_ann = pg.obj.get("/Annots") is not None
        kinds.append("content" if (has_text or has_img or has_ann or data == b"?") else "empty")
    return kinds

def account(path, fmt, cell, mutant=None):
    """cell: dict with raised(bool) and pages(list[str]). Returns dict(units=[status...], raised_msg). Raises ConservationError when units don't conserve."""
    if cell.get("raised"): return dict(units=[], loud="loader raised")
    pages = cell["pages"]
    if mutant == "M1": return dict(units=["read"] * len(pages), loud=None)  # no accounting
    if fmt == "pdf":
        kinds = _pdf_accountant(path)
        if len(kinds) != len(pages): raise ConservationError("page count %d != accountant %d" % (len(pages), len(kinds)))
        st = []
        for k, t in zip(kinds, pages):
            if t.strip(): st.append("read")
            elif k == "empty": st.append("declared_empty")
            else: st.append("declared_empty" if mutant == "M2" else "declared_unreadable")
        return dict(units=st, loud=None)
    if fmt == "docx":
        z = zipfile.ZipFile(path); n_in = 0
        for nm in z.namelist():
            if re.match(r"word/(document|header\d*|footer\d*)\.xml$", nm):
                n_in += sum(len(re.sub(r"\s", "", t)) for t in re.findall(r"<w:t[^>]*>([^<]*)</w:t>", z.read(nm).decode("utf8")))
        n_out = len(re.sub(r"\s", "", "".join(pages)))
        if n_out != n_in:
            if mutant == "M2": return dict(units=["declared_empty"], loud=None)
            raise ConservationError("chars in %d != chars read %d" % (n_in, n_out))
        return dict(units=["read"], loud=None)
    if fmt == "txt":
        b = open(path, "rb").read()
        try:
            ref = b.decode("utf-16") if b[:2] in (b"\xff\xfe", b"\xfe\xff") else b.decode("utf-8")
        except UnicodeDecodeError:
            if mutant == "M2": return dict(units=["declared_empty"], loud=None)
            raise ConservationError("encoding not established (not BOM utf-16, not strict utf-8)")
        out = "".join(pages)
        if out != ref and out.lstrip("﻿") != ref.lstrip("﻿"):
            if mutant == "M2": return dict(units=["declared_empty"], loud=None)
            raise ConservationError("decoded text differs from reference decode (len %d vs %d)" % (len(out), len(ref)))
        return dict(units=["read"], loud=None)
    raise KeyError(fmt)
