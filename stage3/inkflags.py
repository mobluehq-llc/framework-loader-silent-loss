"""W2 branch helper: per-page flags for ink the token reference cannot read. Added for the red-team S1 (PREREG_REDTEAM.md)."""
import re, pikepdf
PATHOPS = {"f", "F", "f*", "B", "B*", "b", "b*", "S", "s", "sh"}
def page_flags(path):
    pdf = pikepdf.open(path); out = []
    for pg in pdf.pages:
        paint = inline = do = False
        try:
            for ops, op in pikepdf.parse_content_stream(pg):
                o = str(op)
                if o in PATHOPS: paint = True
                elif o in ("BI", "ID", "INLINE IMAGE") or isinstance(op, pikepdf.ContentStreamInlineImage): inline = True
                elif o == "Do": do = True
        except Exception: paint = True
        for ops_op in []: pass
        badfont = False
        res = pg.obj.get("/Resources"); fonts = res.get("/Font") if res is not None else None
        if fonts is not None:
            for k in fonts.keys():
                f = fonts[k]; st = str(f.get("/Subtype", ""))
                if st == "/Type0" or st == "/Type3" or (st in ("/Type1", "/TrueType", "/MMType1") and f.get("/Encoding") is None): badfont = True
        out.append(dict(paint=paint, inline=inline, do=do, badfont=badfont, unreadable_ink=paint or inline or do or badfont))
    return out
