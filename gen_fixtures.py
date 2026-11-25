"""AG fixture generator. Ground truth is recorded at generation time in <id>.json manifests.
usage: gen_fixtures.py --seed N --out DIR"""
import argparse, json, os, random, string, io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.pdfencrypt import StandardEncryption
from PIL import Image, ImageDraw
from reportlab.lib.utils import ImageReader
import docx

class Tok:
    def __init__(s, rng): s.r = rng; s.used = set()
    def word(s, mid=None):
        while True:
            n = s.r.randint(8, 11)
            w = s.r.choice(string.ascii_lowercase) + "".join(s.r.choice(string.ascii_lowercase + string.digits) for _ in range(n - 1))
            if mid:
                i = s.r.randint(2, len(w) - 3); w = w[:i] + mid + w[i + 1:]
            if w not in s.used: s.used.add(w); return w
    def words(s, n, mid=None): return [s.word(mid) for _ in range(n)]

def chars(words): return len(" ".join(words))

def draw_words(c, words, x=50, y=740, rot_mode=None):
    t = c.beginText(x, y); t.setFont("Helvetica", 10)
    if rot_mode is not None: t.setTextRenderMode(rot_mode)
    for i in range(0, len(words), 8): t.textLine(" ".join(words[i:i+8]))
    c.drawText(t)

def img_of(words):
    im = Image.new("RGB", (900, 40 * (len(words) // 8 + 2)), "white"); d = ImageDraw.Draw(im)
    for k, i in enumerate(range(0, len(words), 8)): d.text((10, 10 + 36 * k), " ".join(words[i:i+8]), fill="black")
    return im

def pdf(path, units, rotate=None, enc=None, hidden=False):
    c = canvas.Canvas(path, pagesize=letter, pageCompression=0, encrypt=enc)
    form_n = 0
    for i, u in enumerate(units):
        k, w = u["kind"], u["words"]
        if k == "text": draw_words(c, w)
        elif k == "image": c.drawImage(ImageReader(img_of(w)), 40, 400, width=520, height=300)
        elif k == "hidden":
            c.drawImage(ImageReader(img_of(w)), 40, 400, width=520, height=300); draw_words(c, w, rot_mode=3)
        elif k == "form":
            for j, wd in enumerate(w):
                c.acroForm.textfield(name=f"f{i}_{j}", value=wd, x=40 + 130 * (j % 4), y=700 - 30 * (j // 4), width=120, height=22, borderStyle="inset", forceBorder=True)
        if rotate: c.setPageRotation(rotate[i % len(rotate)])
        c.showPage()
    c.save()

def manifest(fid, path, fmt, units, **kw):
    allw = [w for u in units for w in u["words"]]
    m = dict(id=fid, path=os.path.basename(path), format=fmt, page_count=len(units) if fmt == "pdf" else None, units=units,
             total_words=len(allw), total_chars=chars(allw), **kw)
    json.dump(m, open(path + ".json", "w"), indent=1)

def textunits(T, n, per=120, kind="text"): return [dict(kind=kind, words=T.words(per)) for _ in range(n)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    T = Tok(random.Random(a.seed)); P = lambda n: os.path.join(a.out, n)
    def mk(fid, units, **kw):
        p = P(fid + ".pdf"); pdf(p, units, **{k: v for k, v in kw.items() if k in ("rotate", "enc")}); manifest(fid, p, "pdf", units, note=kw.get("note", "")); return p
    mk("P01_text_10p", textunits(T, 10))
    mk("P02_text_200p", textunits(T, 200, 60))
    u = [dict(kind="blank", words=[]) if i in (1, 2, 6, 11) else dict(kind="text", words=T.words(100)) for i in range(12)]
    mk("P03_blank_interleaved_12p", u)
    mk("P04_rotated_10p", textunits(T, 10, 100), rotate=[90, 180, 270, 0])
    mk("P05_encrypted_owner_8p", textunits(T, 8, 100), enc=StandardEncryption("", ownerPassword="own-pw", canPrint=1, strength=128))
    mk("P06_hidden_layer_8p", textunits(T, 8, 80, "hidden"))
    mk("P07_image_only_8p", textunits(T, 8, 80, "image"))
    kinds = ["text", "image", "blank"]
    u = [dict(kind=kinds[i % 3], words=[] if kinds[i % 3] == "blank" else T.words(80)) for i in range(12)]
    mk("P08_mixed_12p", u)
    mk("P09_form_only_6p", textunits(T, 6, 16, "form"))
    mk("P10_encrypted_user_6p", textunits(T, 6, 100), enc=StandardEncryption("userpw", ownerPassword="own-pw", canPrint=1, strength=128))
    p = mk("P11_truncated_10p", textunits(T, 10)); b = open(p, "rb").read(); open(p, "wb").write(b[: int(len(b) * 0.6)])
    mk("P12_single_blank_1p", [dict(kind="blank", words=[])])
    mk("P13_single_text_1p", textunits(T, 1, 100))
    # DOCX
    def dx(fid, build):
        d = docx.Document(); units = build(d); p = P(fid + ".docx"); d.save(p); manifest(fid, p, "docx", units)
    def body(d):
        w = T.words(300); [d.add_paragraph(" ".join(w[i:i+10])) for i in range(0, 300, 10)]; return [dict(kind="body", words=w)]
    dx("D01_body_only", body)
    def tables(d):
        bw = T.words(60); d.add_paragraph(" ".join(bw)); units = [dict(kind="body", words=bw)]
        for _ in range(3):
            t = d.add_table(rows=4, cols=3); tw = T.words(12)
            for i, cell in enumerate(t._cells): cell.text = tw[i]
            units.append(dict(kind="table", words=tw))
        return units
    dx("D02_tables", tables)
    def hf(d):
        bw = T.words(60); d.add_paragraph(" ".join(bw)); s0 = d.sections[0]
        h0, f0 = T.words(5), T.words(5); s0.header.paragraphs[0].text = " ".join(h0); s0.footer.paragraphs[0].text = " ".join(f0)
        s1 = d.add_section(); s1.header.is_linked_to_previous = False; s1.footer.is_linked_to_previous = False
        h1, f1 = T.words(5), T.words(5); s1.header.paragraphs[0].text = " ".join(h1); s1.footer.paragraphs[0].text = " ".join(f1)
        bw2 = T.words(40); d.add_paragraph(" ".join(bw2))
        return [dict(kind="body", words=bw + bw2), dict(kind="header", words=h0 + h1), dict(kind="footer", words=f0 + f1)]
    dx("D03_header_footer", hf)
    def nested(d):
        bw = T.words(40); d.add_paragraph(" ".join(bw)); t = d.add_table(rows=2, cols=2); ow = T.words(4); iw = T.words(6)
        t.cell(0, 0).text = ow[0]; t.cell(0, 1).text = ow[1]; t.cell(1, 0).text = ow[2]
        c = t.cell(1, 1); c.text = ow[3]; nt = c.add_table(rows=2, cols=3)
        for i, cell in enumerate(nt._cells): cell.text = iw[i]
        c.add_paragraph("")
        return [dict(kind="body", words=bw), dict(kind="table", words=ow + iw)]
    dx("D04_nested_table", nested)
    # TXT
    def tx(fid, enc, mid=None, mix=False):
        w = T.words(200); k = []
        if mid:
            idx = list(range(0, 200, 4)); 
            for i in idx: w[i] = T.word(mid)
        text = " ".join(w) + "\n"; p = P(fid + ".txt")
        if mix:  # utf-8 file, but the accented tokens are written as latin-1 bytes
            out = b""
            for i, wd in enumerate(w): out += (wd.encode("latin-1") if mid and mid in wd else wd.encode("utf-8")) + b" "
            open(p, "wb").write(out.rstrip() + b"\n")
        else: open(p, "wb").write(text.encode(enc))
        manifest(fid, p, "txt", [dict(kind="text", words=w)], encoding=enc)
    tx("T01_utf8", "utf-8"); tx("T02_utf16_bom", "utf-16")
    tx("T03_latin1", "latin-1", mid="é"); tx("T04_cp1252", "cp1252", mid="’")
    tx("T05_mixed_encoding", "utf-8", mid="é", mix=True)
    print("ok", a.out, len(os.listdir(a.out)))

if __name__ == "__main__": main()
