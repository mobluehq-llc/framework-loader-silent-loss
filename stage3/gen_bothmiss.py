"""S1 both-readers-miss fixtures. usage: gen_bothmiss.py --seed N --out DIR. Truth: manifest units = [{'A':[words], 'B':[words]}] per page; B is the span the reference reader cannot read."""
import argparse, json, os, random, string
import pymupdf
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image, ImageDraw
H = 792
def words(R, used, n):
    out = []
    while len(out) < n:
        w = R.choice(string.ascii_lowercase) + "".join(R.choice(string.ascii_lowercase + string.digits) for _ in range(R.randint(7, 10)))
        if w not in used: used.add(w); out.append(w)
    return out
def lines(w): return [" ".join(w[i:i + 6]) for i in range(0, len(w), 6)]
def draw_literal(c, w, y):
    t = c.beginText(50, y); t.setFont("Helvetica", 10)
    for l in lines(w): t.textLine(l)
    c.drawText(t)
def draw_ttf(c, w, y):
    t = c.beginText(50, y); t.setFont("ArialTT", 10)
    for l in lines(w): t.textLine(l)
    c.drawText(t)
def draw_img(c, w, y):
    ls = lines(w); im = Image.new("RGB", (700, 30 * len(ls) + 20), "white"); d = ImageDraw.Draw(im)
    for k, l in enumerate(ls): d.text((10, 10 + 28 * k), l, fill="black")
    c.drawImage(ImageReader(im), 40, y - 30 * len(ls) - 20, width=420, height=(30 * len(ls) + 20) * 420 / 700)
def draw_outline(c, w, y):
    d = pymupdf.open(); pg = d.new_page(width=612, height=792)
    for k, l in enumerate(lines(w)): pg.insert_text((50, 60 + 14 * k), l, fontsize=10, fontname="helv")
    svg = pg.get_svg_image(text_as_path=True); d2 = pymupdf.open(stream=svg.encode(), filetype="svg"); p2 = pymupdf.open("pdf", d2.convert_to_pdf())[0]
    n = 0
    for dr in p2.get_drawings():
        if dr.get("fill") is None: continue
        p = c.beginPath(); cur = None
        for it in dr["items"]:
            if it[0] == "l":
                if cur is None or (abs(cur[0] - it[1].x) > 1e-3 or abs(cur[1] - it[1].y) > 1e-3): p.moveTo(it[1].x, y - it[1].y + 60)
                p.lineTo(it[2].x, y - it[2].y + 60); cur = (it[2].x, it[2].y)
            elif it[0] == "c":
                if cur is None or (abs(cur[0] - it[1].x) > 1e-3 or abs(cur[1] - it[1].y) > 1e-3): p.moveTo(it[1].x, y - it[1].y + 60)
                p.curveTo(it[2].x, y - it[2].y + 60, it[3].x, y - it[3].y + 60, it[4].x, y - it[4].y + 60); cur = (it[4].x, it[4].y)
            elif it[0] == "re": r = it[1]; p.rect(r.x0, y - r.y1 + 60, r.width, r.height)
        if dr.get("closePath"): p.close()
        c.setFillColorRGB(0, 0, 0); c.drawPath(p, fill=1, stroke=0); n += 1
    assert n > 0, "no outlines produced"
CLASSES = {"BM1_ttf_span": ("A", draw_ttf), "BM7_ttf_no_tounicode": ("A", draw_ttf), "BM2_image_span": ("A", draw_img), "BM3_outline_span": ("A", draw_outline),
           "BM4_outline_only": (None, draw_outline), "BM5_image_only": (None, draw_img), "BM6_blank": (None, None)}
def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int); ap.add_argument("--out"); a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    R = random.Random(a.seed); used = set(); pdfmetrics.registerFont(TTFont("ArialTT", "/System/Library/Fonts/Supplemental/Arial.ttf"))
    for cid, (hasA, fn) in CLASSES.items():
        n = R.randint(3, 8); units = []; p = os.path.join(a.out, cid + ".pdf"); c = canvas.Canvas(p, pagesize=letter, pageCompression=0)
        for i in range(n):
            A = words(R, used, R.randint(30, 60)) if hasA else []; B = words(R, used, R.randint(30, 60)) if fn else []
            if A: draw_literal(c, A, 740)
            if fn: fn(c, B, 500)
            c.showPage(); units.append(dict(A=A, B=B))
        c.save()
        if cid == "BM7_ttf_no_tounicode":
            import pikepdf
            pdf = pikepdf.open(p, allow_overwriting_input=True); k = 0
            for obj in pdf.objects:
                if isinstance(obj, pikepdf.Dictionary) and "/ToUnicode" in obj: del obj["/ToUnicode"]; k += 1
            assert k > 0; pdf.save(p)
        json.dump(dict(id=cid, units=units, page_count=n), open(p + ".json", "w"))
main()
