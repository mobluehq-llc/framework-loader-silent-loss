"""Post-hoc (not registered): is PyMuPDF's P4 loss caused by clipping to the page box? Text of P4 pages with /Rotate 90 is drawn at y=740 on a page whose
MediaBox is 792 x 612 (generator side effect of reportlab's setPageRotation), i.e. partly OUTSIDE the box. Default get_text clips to the box (flags with
TEXT_MEDIABOX_CLIP); clip=INFINITE_RECT does not (checked: 16 vs 104 words on one page). usage: .venv/bin/python -W ignore stage3/p4_clip_check.py > results/p4_clip_check.txt"""
import os, json, collections, pymupdf
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); tot = collections.Counter(); boxes = collections.Counter()
for sd in range(20261401, 20261421):
    p = None
    for d in ("fixtures3_fw", "fixtures3_fw2"):
        q = os.path.join(H, d, str(sd), "P04_rotated.pdf")
        if os.path.exists(q): p = q
    man = json.load(open(p + ".json")); truth = [w for u in man["units"] for w in u["words"]]; a = set(); b = set(); doc = pymupdf.open(p)
    for pg in doc:
        boxes[(pg.rotation, tuple(pg.mediabox), tuple(pg.cropbox) == tuple(pg.mediabox))] += 1
        a |= {w[4] for w in pg.get_text("words")}; ws = pg.get_text("words", clip=pymupdf.INFINITE_RECT()); b |= {w[4] for w in ws}
        for w in ws:
            if w[4] not in {x[4] for x in pg.get_text("words")}: tot["extra_total"] += 1; tot["extra_outside_page"] += not pg.rect.intersects(pymupdf.Rect(w[:4]))
    tot["words"] += len(truth); tot["default"] += sum(w in a for w in truth); tot["no_box_clip"] += sum(w in b for w in truth)
print("PyMuPDF", pymupdf.version[0], "20 seeds, P04")
for k, v in sorted(boxes.items()): print("pages with /Rotate %d, MediaBox %s, CropBox==MediaBox %s: %d" % (k[0], k[1], k[2], v))
print("words returned only with the clip off: %d, of which entirely outside the page rectangle: %d" % (tot["extra_total"], tot["extra_outside_page"]))
print("known words %d; returned by default get_text %d (%.2f); returned with the box clip off %d (%.2f)" % (tot["words"], tot["default"], tot["default"] / tot["words"], tot["no_box_clip"], tot["no_box_clip"] / tot["words"]))
