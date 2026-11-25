"""Stage-2 fixture generator. usage: gen2.py --seed N --out DIR  (one file per class, randomised sizes, ground truth in manifests)"""
import argparse, json, os, random, string, html as _h
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.lib.utils import ImageReader
from PIL import Image, ImageDraw
import docx, pptx
from pptx.util import Inches

class Tok:
    def __init__(s, rng): s.r = rng; s.used = set()
    def word(s, mid=None):
        while True:
            n = s.r.randint(8, 11)
            w = s.r.choice(string.ascii_lowercase) + "".join(s.r.choice(string.ascii_lowercase + string.digits) for _ in range(n - 1))
            if mid: i = s.r.randint(2, len(w) - 3); w = w[:i] + mid + w[i + 1:]
            if w not in s.used: s.used.add(w); return w
    def words(s, n, mid=None, dup=True):
        w = [s.word(mid) for _ in range(n)]
        if dup and n >= 10:  # about 10 percent repeated once inside the unit: truth is a multiset
            w += [s.r.choice(w) for _ in range(max(1, n // 10))]; s.r.shuffle(w)
        return w

def draw_words(c, words, rm=None):
    t = c.beginText(50, 740); t.setFont("Helvetica", 10)
    if rm is not None: t.setTextRenderMode(rm)
    for i in range(0, len(words), 8): t.textLine(" ".join(words[i:i+8]))
    c.drawText(t)

def img_of(words):
    im = Image.new("RGB", (900, 40 * (len(words) // 8 + 2)), "white"); d = ImageDraw.Draw(im)
    for k, i in enumerate(range(0, len(words), 8)): d.text((10, 10 + 36 * k), " ".join(words[i:i+8]), fill="black")
    return im

def pdf(path, units, rotate=None):
    c = canvas.Canvas(path, pagesize=letter, pageCompression=0)
    for i, u in enumerate(units):
        k, w = u["kind"], u["words"]
        if k == "text": draw_words(c, w)
        elif k == "image": c.drawImage(ImageReader(img_of(w)), 40, 400, width=520, height=300)
        elif k == "hidden": c.drawImage(ImageReader(img_of(w)), 40, 400, width=520, height=300); draw_words(c, w, 3)
        elif k == "form":
            for j, wd in enumerate(w): c.acroForm.textfield(name=f"f{i}_{j}", value=wd, x=40 + 130 * (j % 4), y=700 - 30 * (j // 4), width=120, height=22, borderStyle="inset", forceBorder=True)
        if rotate: c.setPageRotation(rotate[i % len(rotate)])
        c.showPage()
    c.save()

def manifest(fid, path, fmt, units, **kw):
    allw = [w for u in units for w in u["words"]]
    json.dump(dict(id=fid, path=os.path.basename(path), format=fmt, page_count=len(units) if fmt == "pdf" else None, units=units, total_words=len(allw), **kw), open(path + ".json", "w"), indent=1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, required=True); ap.add_argument("--out", required=True)
    a = ap.parse_args(); os.makedirs(a.out, exist_ok=True)
    R = random.Random(a.seed); T = Tok(R); P = lambda n: os.path.join(a.out, n)
    tu = lambda n, per=None, kind="text": [dict(kind=kind, words=T.words(per or R.randint(60, 140))) for _ in range(n)]
    def mk(fid, units, **kw):
        p = P(fid + ".pdf"); pdf(p, units, **kw); manifest(fid, p, "pdf", units); return p
    mk("P01_text", tu(R.randint(5, 15)))
    n = R.randint(8, 14); blanks = set(R.sample(range(n), R.randint(2, 4)))
    mk("P03_blank_interleaved", [dict(kind="blank", words=[]) if i in blanks else dict(kind="text", words=T.words(R.randint(60, 120))) for i in range(n)])
    mk("P04_rotated", tu(R.randint(5, 12)), rotate=R.choice([[90, 180, 270, 0], [90], [270, 0], [180, 90]]))
    mk("P06_hidden_layer", tu(R.randint(5, 10), R.randint(40, 80), "hidden"))
    mk("P07_image_only", tu(R.randint(5, 10), R.randint(40, 80), "image"))
    mk("P09_form_only", tu(R.randint(4, 8), R.randint(8, 16), "form"))
    p = mk("P11_truncated", tu(R.randint(6, 12))); b = open(p, "rb").read(); open(p, "wb").write(b[: int(len(b) * R.uniform(0.5, 0.7))])
    def dx(fid, build):
        d = docx.Document(); units = build(d); p = P(fid + ".docx"); d.save(p); manifest(fid, p, "docx", units)
    def para(d, w): [d.add_paragraph(" ".join(w[i:i+10])) for i in range(0, len(w), 10)]
    def body(d): w = T.words(R.randint(150, 400)); para(d, w); return [dict(kind="body", words=w)]
    dx("D01_body", body)
    def tables(d):
        bw = T.words(R.randint(30, 80)); para(d, bw); units = [dict(kind="body", words=bw)]
        for _ in range(R.randint(1, 4)):
            r, cc = R.randint(2, 5), R.randint(2, 4); t = d.add_table(rows=r, cols=cc); tw = [T.word() for _ in range(r * cc)]
            for i, cell in enumerate(t._cells): cell.text = tw[i]
            units.append(dict(kind="table", words=tw))
        return units
    dx("D02_tables", tables)
    def hf(d):
        bw = T.words(R.randint(30, 80)); para(d, bw); s0 = d.sections[0]; h, f = [], []
        a_, b_ = T.words(5, dup=False), T.words(5, dup=False); s0.header.paragraphs[0].text = " ".join(a_); s0.footer.paragraphs[0].text = " ".join(b_); h += a_; f += b_
        for _ in range(R.randint(1, 2)):
            s = d.add_section(); s.header.is_linked_to_previous = False; s.footer.is_linked_to_previous = False
            a_, b_ = T.words(5, dup=False), T.words(5, dup=False); s.header.paragraphs[0].text = " ".join(a_); s.footer.paragraphs[0].text = " ".join(b_); h += a_; f += b_
            w2 = T.words(R.randint(20, 40)); para(d, w2); bw += w2
        return [dict(kind="body", words=bw), dict(kind="header", words=h), dict(kind="footer", words=f)]
    dx("D03_header_footer", hf)
    def nested(d):
        bw = T.words(R.randint(20, 50)); para(d, bw); t = d.add_table(rows=2, cols=2); ow = [T.word() for _ in range(4)]; iw = [T.word() for _ in range(6)]
        t.cell(0, 0).text = ow[0]; t.cell(0, 1).text = ow[1]; t.cell(1, 0).text = ow[2]
        c = t.cell(1, 1); c.text = ow[3]; nt = c.add_table(rows=2, cols=3)
        for i, cell in enumerate(nt._cells): cell.text = iw[i]
        c.add_paragraph("")
        return [dict(kind="body", words=bw), dict(kind="table", words=ow + iw)]
    dx("D04_nested_table", nested)
    # PPTX
    def px(fid, build):
        pr = pptx.Presentation(); pr.slide_width, pr.slide_height = Inches(10), Inches(7.5); units = build(pr); p = P(fid + ".pptx"); pr.save(p); manifest(fid, p, "pptx", units)
    blank = lambda pr: pr.slides.add_slide(pr.slide_layouts[6])
    def tbox(shapes, w, x=0.5, y=0.5):
        tb = shapes.add_textbox(Inches(x), Inches(y), Inches(8), Inches(3)); tb.text_frame.word_wrap = True; tb.text_frame.text = " ".join(w)
    def s_text(pr):
        u = []
        for _ in range(R.randint(3, 8)): s = blank(pr); w = T.words(R.randint(30, 80)); tbox(s.shapes, w); u.append(dict(kind="body", words=w))
        return u
    px("S01_textboxes", s_text)
    def s_table(pr):
        u = []
        for _ in range(R.randint(2, 5)):
            s = blank(pr); w = T.words(R.randint(20, 40)); tbox(s.shapes, w); u.append(dict(kind="body", words=w))
            r, cc = R.randint(2, 4), R.randint(2, 4); gf = s.shapes.add_table(r, cc, Inches(0.5), Inches(4), Inches(8), Inches(2)); tw = [T.word() for _ in range(r * cc)]
            for i in range(r * cc): gf.table.cell(i // cc, i % cc).text = tw[i]
            u.append(dict(kind="table", words=tw))
        return u
    px("S02_table", s_table)
    def s_group(pr):
        u = []
        for _ in range(R.randint(2, 5)):
            s = blank(pr); w = T.words(R.randint(20, 40)); tbox(s.shapes, w); u.append(dict(kind="body", words=w))
            g = s.shapes.add_group_shape(); gw = T.words(R.randint(10, 20)); tbox(g.shapes, gw, 0.5, 4); u.append(dict(kind="group", words=gw))
        return u
    px("S03_grouped_shapes", s_group)
    def s_notes(pr):
        u = []
        for _ in range(R.randint(2, 5)):
            s = blank(pr); w = T.words(R.randint(20, 40)); tbox(s.shapes, w); u.append(dict(kind="body", words=w))
            nw = T.words(R.randint(15, 30)); s.notes_slide.notes_text_frame.text = " ".join(nw); u.append(dict(kind="notes", words=nw))
        return u
    px("S04_notes", s_notes)
    # HTML
    def ht(fid, build):
        p = P(fid + ".html"); units, s = build(); open(p, "w", encoding="utf-8").write(s); manifest(fid, p, "html", units)
    wrap = lambda b, head="": "<!DOCTYPE html><html><head><meta charset='utf-8'><title>t</title>%s</head><body>%s</body></html>" % (head, b)
    ps = lambda w: "".join("<p>%s</p>" % " ".join(w[i:i+10]) for i in range(0, len(w), 10))
    def h1(): w = T.words(R.randint(100, 300)); return [dict(kind="body", words=w)], wrap("<article>%s</article>" % ps(w))
    ht("H01_body", h1)
    def h2():
        bw = T.words(R.randint(30, 80)); r, cc = R.randint(2, 5), R.randint(2, 4); tw = [T.word() for _ in range(r * cc)]; lw = [T.word() for _ in range(R.randint(3, 8))]
        tb = "<table>" + "".join("<tr>" + "".join("<td>%s</td>" % tw[i * cc + j] for j in range(cc)) + "</tr>" for i in range(r)) + "</table>"
        return [dict(kind="body", words=bw), dict(kind="table", words=tw), dict(kind="body", words=lw)], wrap("<article>%s%s<ul>%s</ul></article>" % (ps(bw), tb, "".join("<li>%s</li>" % x for x in lw)))
    ht("H02_table_list", h2)
    def h3():
        bw = T.words(R.randint(100, 250)); nv, ft, sd = T.words(8, dup=False), T.words(8, dup=False), T.words(8, dup=False)
        return [dict(kind="body", words=bw), dict(kind="boilerplate", words=nv + ft + sd)], wrap("<nav>%s</nav><aside>%s</aside><article>%s</article><footer>%s</footer>" % (" ".join(nv), " ".join(sd), ps(bw), " ".join(ft)))
    ht("H03_boilerplate", h3)
    def h4():
        bw = T.words(R.randint(40, 100)); dw = T.words(R.randint(20, 60)); js = json_list = "[" + ",".join('"%s"' % x[::-1] for x in dw) + "]"
        return [dict(kind="body", words=bw), dict(kind="dynamic", words=dw)], wrap("<article>%s</article><div id='x'></div>" % ps(bw)) .replace("</body>", "<script>var r=%s;document.getElementById('x').textContent=r.map(function(s){return s.split('').reverse().join('')}).join(' ');</script></body>" % js)
    ht("H04_js_rendered", h4)
    def h5():
        w = T.words(R.randint(100, 250)); out = []
        for i, x in enumerate(w):
            if i % 5 == 0:
                x = T.word("é"); w[i] = x; x = x.replace("é", R.choice(["&eacute;", "&#233;", "&#xe9;"]))
            out.append(x)
        return [dict(kind="entity", words=w)], wrap("<article>%s</article>" % ps(out))
    ht("H05_entities", h5)
    def h6():
        bw = T.words(R.randint(60, 120)); hw = T.words(R.randint(20, 40))
        return [dict(kind="body", words=bw), dict(kind="csshidden", words=hw)], wrap("<article>%s</article><div style='display:none'>%s</div>" % (ps(bw), " ".join(hw)))
    ht("H06_css_hidden", h6)
    # TXT
    def tx(fid, enc, mid=None, mix=False):
        w = T.words(R.randint(100, 300), dup=False)
        if mid:
            for i in range(0, len(w), 4): w[i] = T.word(mid)
        w += [R.choice(w) for _ in range(len(w) // 10)]; R.shuffle(w); p = P(fid + ".txt")
        if mix: open(p, "wb").write(b" ".join(x.encode("latin-1") if (mid and mid in x) else x.encode("utf-8") for x in w) + b"\n")
        else: open(p, "wb").write((" ".join(w) + "\n").encode(enc))
        manifest(fid, p, "txt", [dict(kind="text", words=w)], encoding=enc)
    tx("T01_utf8", "utf-8"); tx("T02_utf16_bom", "utf-16"); tx("T03_latin1", "latin-1", "é"); tx("T04_cp1252", "cp1252", "’"); tx("T05_mixed_encoding", "utf-8", "é", True)

if __name__ == "__main__": main()
