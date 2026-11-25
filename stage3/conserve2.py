"""Stage-2 text-level conservation. Independent reader per format; unit is 'read' only if its token (or char) multiset is fully recovered."""
import re, zipfile, html, collections
from html.parser import HTMLParser
TOK = re.compile(r"[a-z0-9é’]+")
def toks(s): return collections.Counter(TOK.findall(s.lower()))
def chars(s): return collections.Counter(c for c in s.lower() if c.isalnum())
def recall(R, O):
    n = sum(R.values()); return 1.0 if n == 0 else sum(min(v, O[k]) for k, v in R.items()) / n
class ConservationError(Exception): pass

def _pdf_ref(path):
    """-> list of (Counter, kind) per page, kind in content/empty. Raises ConservationError on file-level problems."""
    import pikepdf
    raw = open(path, "rb").read()
    if raw.rstrip()[-5:] != b"%%EOF": raise ConservationError("file truncated: no %%EOF")
    try: pdf = pikepdf.open(path)
    except pikepdf.PasswordError: raise ConservationError("password required")
    except Exception as e: raise ConservationError("unopenable: %s" % type(e).__name__)
    if pdf.check_pdf_syntax(): raise ConservationError("structure problems: repair needed")
    out = []
    for pg in pdf.pages:
        strs = []; has_img = has_ann = False
        try:
            for ops, op in pikepdf.parse_content_stream(pg):
                o = str(op)
                if o in ("Tj", "'", '"') and ops and isinstance(ops[-1], pikepdf.String): strs.append(bytes(ops[-1]).decode("latin-1"))
                elif o == "TJ" and ops:
                    strs.append("".join(bytes(x).decode("latin-1") if isinstance(x, pikepdf.String) else (" " if float(x) < -200 else "") for x in ops[0]))
        except Exception as e: raise ConservationError("content stream unparseable: %s" % type(e).__name__)
        res = pg.obj.get("/Resources"); xo = res.get("/XObject") if res is not None else None
        has_img = xo is not None and len(xo.keys()) > 0
        an = pg.obj.get("/Annots")
        if an is not None:
            has_ann = True
            for a in an:
                v = a.get("/V")
                if v is not None: strs.append(str(v))
        c = collections.Counter()
        for s in strs: c += toks(s)
        out.append((c, "content" if (c or has_img or has_ann) else "empty"))
    return out

def _xml_t(path, pat, tag):
    z = zipfile.ZipFile(path); c = collections.Counter()
    for nm in z.namelist():
        if re.match(pat, nm):
            for t in re.findall(r"<%s(?:\s[^>]*)?>([^<]*)</%s>" % (tag, tag), z.read(nm).decode("utf8")): c += toks(html.unescape(t))
    return c

class _H(HTMLParser):
    def __init__(s): super().__init__(convert_charrefs=True); s.skip = 0; s.buf = []; s.script = False
    def handle_starttag(s, t, a):
        if t in ("script", "style", "head", "title"): s.skip += 1
    def handle_endtag(s, t):
        if t in ("script", "style", "head", "title") and s.skip: s.skip -= 1
    def handle_data(s, d):
        if not s.skip: s.buf.append(d)

def _html_ref(path):
    src = open(path, encoding="utf-8").read(); h = _H(); h.feed(src)
    dyn = any(len(b.strip()) >= 20 for b in re.findall(r"<script[^>]*>(.*?)</script>", src, flags=re.S | re.I))
    return toks(" ".join(h.buf)), dyn

def _txt_ref(path):
    b = open(path, "rb").read()
    try: return toks(b.decode("utf-16") if b[:2] in (b"\xff\xfe", b"\xfe\xff") else b.decode("utf-8"))
    except UnicodeDecodeError: raise ConservationError("encoding not established (not BOM utf-16, not strict utf-8)")

def reference(path, fmt):
    """Whole-file reference Counter (for the instrument check) and pdf per-page list."""
    if fmt == "pdf": pp = _pdf_ref(path); c = collections.Counter(); [c.update(x[0]) for x in pp]; return c
    if fmt == "docx": return _xml_t(path, r"word/(document|header\d*|footer\d*|footnotes|endnotes)\.xml$", "w:t")
    if fmt == "pptx": return _xml_t(path, r"ppt/(slides/slide|notesSlides/notesSlide)\d+\.xml$", "a:t")
    if fmt == "html": return _html_ref(path)[0]
    if fmt == "txt": return _txt_ref(path)

def account(path, fmt, lid, cell, mutant=None, docgrain=()):
    """-> dict(units=[status...], loud=None|msg). status in read/declared_empty/declared_unreadable. mutant in None,M1,M2,M3."""
    if cell.get("raised"): return dict(units=[], loud="loader raised")
    pages = cell["pages"]
    if mutant == "M1": return dict(units=["read"] * (len(pages) if fmt == "pdf" and lid not in docgrain else 1), loud=None)
    def ok(R, text):
        return (recall(chars("".join(R.elements())), chars(text)) == 1.0) if mutant == "M3" else recall(R, toks(text)) == 1.0
    def fail(msg):
        if mutant == "M2": return "declared_empty"
        raise ConservationError(msg)
    if fmt == "pdf":
        ref = _pdf_ref(path)
        if lid in docgrain:
            R = collections.Counter(); [R.update(x[0]) for x in ref]
            if not R and any(k == "content" for _, k in ref): return dict(units=["declared_empty" if mutant == "M2" else "declared_unreadable"], loud=None)
            return dict(units=["read" if ok(R, "\n".join(pages)) else fail("doc-level recall < 1")], loud=None)
        if len(ref) != len(pages): raise ConservationError("page count %d != accountant %d" % (len(pages), len(ref)))
        st = []
        for (R, k), t in zip(ref, pages):
            if R: st.append("read" if ok(R, t) else fail("page recall %.2f" % recall(R, toks(t))))
            elif k == "empty": st.append("declared_empty")
            else: st.append("declared_empty" if mutant == "M2" else "declared_unreadable")
        return dict(units=st, loud=None)
    text = "\n".join(pages)
    if fmt == "html":
        R, dyn = _html_ref(path); s = "read" if ok(R, text) else fail("recall < 1")
        return dict(units=[("declared_empty" if mutant == "M2" else "declared_unreadable") if (dyn and s == "read") else s], loud=None)
    R = reference(path, fmt)
    return dict(units=["read" if ok(R, text) else fail("recall < 1")], loud=None)
