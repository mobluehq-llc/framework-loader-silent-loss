"""Writes numbers.tex, table_fw.tex, table_lib.tex for the AG note from stored result files only. usage: python3 paper_note/make_numbers.py
Sources: results/redteam_fw_s2_all.json (framework defaults, seeds 20261401-20), results/main2.json + holdout2.json (library idioms),
results/redteam_s2.json (plain-settings pipeline), results/redteam_p11_main2.json, and literal strings asserted present in
results/redteam_fw_real.txt, redteam_pilot.txt, redteam_bm_summary.txt, paper_note/posthoc_real_html_glue.txt."""
import json, os, collections, math
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = lambda f: os.path.join(H, "results", f); N = os.path.dirname(os.path.abspath(__file__))
def wil(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return max(0, c - h), min(1, c + h)
def agg(cells):
    A = collections.defaultdict(lambda: dict(n=0, f=0, t=0, silent=0, raised=0, unread=0))
    for c in cells:
        a = A[(c["loader"], c["fixture"][:3])]; a["n"] += 1; a["raised"] += bool(c["raised"])
        if c["raised"]: continue
        core = c.get("recall_core")
        if core is None:
            ks = [v for k, v in c["by_kind"].items() if k not in ("image", "form", "dynamic", "boilerplate", "csshidden")]; core = (sum(v["found"] for v in ks), sum(v["total"] for v in ks))
        a["f"] += core[0]; a["t"] += core[1]; a["silent"] += bool(c.get("silent_core", c.get("loss_core"))); a["unread"] += bool(c.get("silent_unread", c.get("loss_unread")))
    return A
fw = agg(json.load(open(R("redteam_fw_s2_all.json")))); m2 = agg(json.load(open(R("main2.json")))["cells"]); h2 = agg(json.load(open(R("holdout2.json")))["cells"]); s2 = agg(json.load(open(R("redteam_s2.json")))["cells"]); fw2 = agg(json.load(open(R("fw2_main.json"))))
M = {}
def put(k, v): M[k] = v
def rec(a): return "%.2f" % (a["f"] / a["t"])
def tot(A, l):
    r = [v for (ld, _), v in A.items() if ld == l]; return dict(n=sum(x["n"] for x in r), f=sum(x["f"] for x in r), t=sum(x["t"] for x in r), silent=sum(x["silent"] for x in r), raised=sum(x["raised"] for x in r))
lc = tot(fw, "lc_html"); assert lc["silent"] == lc["n"] == 120
put("lcHtmlSilent", lc["silent"]); put("lcHtmlRuns", lc["n"]); put("lcHtmlFound", "%d" % lc["f"]); put("lcHtmlTotal", lc["t"]); put("lcHtmlRecall", rec(lc))
cls = [fw[("lc_html", "H0%d" % i)] for i in range(1, 7)]; put("lcHtmlRecMin", min(rec(a) for a in cls)); put("lcHtmlRecMax", max(rec(a) for a in cls))
put("wilTwentyLo", "%.2f" % wil(20, 20)[0]); put("wilFiveLo", "%.2f" % wil(5, 5)[0]); put("wilZeroTwentyHi", "%.2f" % wil(0, 20)[1])
rows = []; clean = []; p4rows = []; p11rows = []
def S(A, l, cs):
    a = dict(n=0, f=0, t=0, silent=0, raised=0)
    for c in cs:
        for k in a: a[k] += A[(l, c)][k]
    return a
def line(name, what, a, tgt, note=""):
    rec_ = "%.2f" % (a["f"] / a["t"]) if a["t"] and a["raised"] < a["n"] else "--"
    tgt.append("%s & %s%s & %d/%d & %d & %s \\\\" % (name, what, note, a["silent"], a["n"], a["raised"], rec_))
def row(tgt, name, A, l, cs, what, note=""): line(name, what, S(A, l, cs), tgt, note)
H6 = ["H01", "H02", "H03", "H04", "H05", "H06"]
# ---- main Table I: loss or rejection only
row(rows, "LangChain \\texttt{BSHTMLLoader}", fw, "lc_html", H6, "HTML, all six classes (H1--H6)")
row(p11rows, "LangChain \\texttt{PyPDFLoader}", fw, "lc_pdf", ["P11"], "PDF, truncated (P11)")
row(rows, "LlamaIndex \\texttt{SimpleDirectoryReader}", fw, "li_txt", ["T02"], "TXT, UTF-16 with BOM (T2)")
row(rows, "", fw, "li_txt", ["T03", "T04", "T05"], "TXT, Latin-1, cp1252, mixed (T3--T5)")
row(rows, "", fw, "li_html", ["H05"], "HTML, character entities (H5)", "$^{a}$"); row(p11rows, "LlamaIndex \\texttt{SimpleDirectoryReader}", fw, "li_pdf", ["P11"], "PDF, truncated (P11)", "$^{c}$")
row(rows, "Docling \\texttt{DocumentConverter}", fw, "docling_docx", ["D03"], "DOCX, headers and footers (D3)"); row(rows, "", fw, "docling_pptx", ["S04"], "PPTX, speaker notes (S4)")
row(rows, "", fw, "docling_pdf", ["P06"], "PDF, hidden text over image (P6)"); row(p11rows, "Docling \\texttt{DocumentConverter}", fw, "docling_pdf", ["P11"], "PDF, truncated (P11)", "$^{d}$")
row(rows, "Haystack \\texttt{DOCXToDocument}", fw2, "hs_docx", ["D03"], "DOCX, headers and footers (D3)"); row(rows, "", fw2, "hs_docx", ["D04"], "DOCX, table nested in a cell (D4)")
row(p11rows, "Haystack \\texttt{PyPDFToDocument}", fw2, "hs_pdf", ["P11"], "PDF, truncated (P11)", "$^{b}$"); row(rows, "Haystack \\texttt{TextFileToDocument}", fw2, "hs_txt", ["T02", "T03", "T04", "T05"], "TXT, four non-UTF-8 classes (T2--T5)", "$^{b}$")
row(rows, "Unstructured \\texttt{partition}", fw2, "un_pptx", ["S04"], "PPTX, speaker notes (S4)"); row(rows, "", fw2, "un_txt", ["T03", "T04", "T05"], "TXT, Latin-1, cp1252, mixed (T3--T5)"); row(p11rows, "Unstructured \\texttt{partition}", fw2, "un_pdf", ["P11"], "PDF, truncated (P11)")
row(rows, "MarkItDown \\texttt{convert}", fw2, "mk_docx", ["D03"], "DOCX, headers and footers (D3)"); row(rows, "", fw2, "mk_txt", ["T03", "T04", "T05"], "TXT, Latin-1, cp1252, mixed (T3--T5)"); row(p11rows, "MarkItDown \\texttt{convert}", fw2, "mk_pdf", ["P11"], "PDF, truncated (P11)")
# ---- supplement: tested, no core loss, and not raised (the controls and every other clean cell)
row(clean, "LangChain \\texttt{PyPDFLoader}", fw, "lc_pdf", ["P01", "P03", "P06"], "PDF, P1, P3, P6")
row(clean, "LangChain \\texttt{Docx2txtLoader}", fw, "lc_docx", ["D01", "D02", "D03", "D04"], "DOCX, all four classes")
row(clean, "LlamaIndex \\texttt{SimpleDirectoryReader}", fw, "li_txt", ["T01"], "TXT, UTF-8 (T1)"); row(clean, "", fw, "li_html", ["H01", "H02", "H03", "H04", "H06"], "HTML, five classes (not H5)")
row(clean, "", fw, "li_pdf", ["P01", "P03", "P06"], "PDF, P1, P3, P6")
d = tot(fw, "li_docx"); p = tot(fw, "li_pptx"); a = dict(n=d["n"] + p["n"], f=d["f"] + p["f"], t=d["t"] + p["t"], silent=d["silent"] + p["silent"], raised=d["raised"] + p["raised"]); line("", "DOCX and PPTX, all eight classes", a, clean)
row(clean, "Docling \\texttt{DocumentConverter}", fw, "docling_docx", ["D01", "D02", "D04"], "DOCX, D1, D2, D4"); row(clean, "", fw, "docling_pptx", ["S01", "S02", "S03"], "PPTX, S1, S2, S3")
row(clean, "", fw, "docling_pdf", ["P01", "P03"], "PDF, P1, P3"); row(clean, "", fw, "docling_html", H6, "HTML, all six classes")
row(clean, "Haystack", fw2, "hs_docx", ["D01", "D02"], "\\texttt{DOCXToDocument}, D1, D2"); row(clean, "", fw2, "hs_html", H6, "\\texttt{HTMLToDocument}, all six classes")
row(clean, "", fw2, "hs_pdf", ["P01", "P03", "P06"], "\\texttt{PyPDFToDocument}, P1, P3, P6"); row(clean, "", fw2, "hs_txt", ["T01"], "\\texttt{TextFileToDocument}, T1")
row(clean, "Unstructured", fw2, "un_docx", ["D01", "D02", "D03", "D04"], "DOCX, all four classes"); row(clean, "", fw2, "un_pptx", ["S01", "S02", "S03"], "PPTX, S1, S2, S3")
row(clean, "", fw2, "un_html", H6, "HTML, all six classes"); row(clean, "", fw2, "un_pdf", ["P01", "P03", "P06"], "PDF, P1, P3, P6"); row(clean, "", fw2, "un_txt", ["T01", "T02"], "TXT, T1, T2")
row(clean, "MarkItDown", fw2, "mk_docx", ["D01", "D02", "D04"], "DOCX, D1, D2, D4"); row(clean, "", fw2, "mk_pptx", ["S01", "S02", "S03", "S04"], "PPTX, all four classes")
row(clean, "", fw2, "mk_html", H6, "HTML, all six classes"); row(clean, "", fw2, "mk_pdf", ["P01", "P03", "P06"], "PDF, P1, P3, P6"); row(clean, "", fw2, "mk_txt", ["T01", "T02"], "TXT, T1, T2")
# ---- AMENDMENT 5: P4 corrected rerun (results/p4fix.json); the original P04 cells are withdrawn and appear nowhere
P4C = collections.defaultdict(lambda: dict(n=0, f=0, t=0, silent=0, raised=0))
for c in json.load(open(R("p4fix.json"))):
    a = P4C[c["loader"]]; a["n"] += 1; a["raised"] += bool(c["raised"])
    if not c["raised"]: a["f"] += c["recall_core"][0]; a["t"] += c["recall_core"][1]; a["silent"] += c["recall_core"][0] < c["recall_core"][1]
for k, nm in (("lc_pdf", "LangChain \\texttt{PyPDFLoader}"), ("li_pdf", "LlamaIndex"), ("docling_pdf", "Docling"), ("hs_pdf", "Haystack \\texttt{PyPDFToDocument}"), ("un_pdf", "Unstructured"), ("mk_pdf", "MarkItDown"), ("pymupdf", "PyMuPDF \\texttt{get\\_text}")):
    line(nm, "PDF, rotated pages, corrected file (P4c)", P4C[k], p4rows)
_u, _m = P4C["un_pdf"], P4C["mk_pdf"]; assert _u["raised"] == _m["raised"] == 0
rows.append("Unstructured, MarkItDown & PDF, rotated pages, corrected file (P4c) & %d/%d, %d/%d & 0 & %.2f, %.2f \\\\" % (_u["silent"], _u["n"], _m["silent"], _m["n"], _u["f"] / _u["t"], _m["f"] / _m["t"]))
assert P4C["un_pdf"]["silent"] == 20 and P4C["mk_pdf"]["silent"] == 15 and all(P4C[k]["silent"] == 0 for k in ("lc_pdf", "li_pdf", "docling_pdf", "hs_pdf", "pymupdf"))
# HTML per-class recall range for LangChain; Haystack/Unstructured/MarkItDown/Docling/LlamaIndex HTML denominators
for fl, A, key in (("hs_html", fw2, "hs"), ("un_html", fw2, "un"), ("mk_html", fw2, "mk"), ("docling_html", fw, "dl"), ("li_html", fw, "li")):
    a = S(A, fl, H6); put(key + "HtmlSilent", a["silent"]); put(key + "HtmlRuns", a["n"])
open(os.path.join(N, "table_fw.tex"), "w").write("\n".join(rows) + "\n"); open(os.path.join(N, "table_fw_clean.tex"), "w").write("\n".join(clean) + "\n"); open(os.path.join(N, "table_fw_p4.tex"), "w").write("\n".join(p4rows) + "\n"); open(os.path.join(N, "table_fw_p11.tex"), "w").write("\n".join(p11rows) + "\n")
rows = []
def lrow(name, l, c, what):
    a, b = m2[(l, c)], h2[(l, c)]; assert a["n"] == b["n"] == 20; rows.append("%s & %s & %d, %d & %s, %s \\\\" % (name, what, a["silent"], b["silent"], rec(a) if a["t"] else "--", rec(b) if b["t"] else "--"))
lrow("python-docx paras.", "docx_paragraphs", "D02", "tables (D2)"); lrow("", "docx_paragraphs", "D03", "header, footer (D3)"); lrow("", "docx_paragraphs", "D04", "nested table (D4)")
lrow("mammoth raw text", "mammoth", "D03", "header, footer (D3)")
lrow("python-pptx frames", "pptx_shapes", "S02", "tables (S2)"); lrow("", "pptx_shapes", "S03", "grouped shapes (S3)"); lrow("", "pptx_shapes", "S04", "speaker notes (S4)")
lrow("PyMuPDF \\texttt{get\\_text}", "pymupdf", "P11", "truncated: damaged-input handling (P11)$^{a}$")
open(os.path.join(N, "table_lib.tex"), "w").write("\n".join(rows) + "\n")
for l in ("docx_full", "docx2txt", "pptx_walk", "markitdown_pptx"):
    for A in (m2, h2): t = tot(A, l); assert t["silent"] == 0 and t["f"] == t["t"], l
for l in ("pypdf", "pypdfium2"):
    for A in (m2, h2): assert A[(l, "P04")]["f"] == A[(l, "P04")]["t"] and A[(l, "P11")]["raised"] == 20
put("muRotMain", rec(m2[("pymupdf", "P04")])); put("muRotHold", rec(h2[("pymupdf", "P04")])); put("muTruncMain", rec(m2[("pymupdf", "P11")])); put("muTruncHold", rec(h2[("pymupdf", "P11")]))
put("muTruncHoldSilent", h2[("pymupdf", "P11")]["silent"]); put("muTruncHoldRaised", h2[("pymupdf", "P11")]["raised"])
p11 = json.load(open(R("redteam_p11_main2.json"))); put("pRepaired", sum(x["is_repaired"] for x in p11)); put("pFiles", len(p11)); put("pZeroPages", sum(1 for x in p11 for r in x["page_recall"] if r == 0)); put("pPages", sum(x["pages_truth"] for x in p11))
assert all(x["pages_truth"] == x["pages_returned"] and x["mupdf_warning_len"] > 0 and x["pypdfium2_raises"] for x in p11)
for l, k in (("docx_full", "cDocx"), ("pptx_walk", "cPptx"), ("bs4_sep", "cHtml"), ("txt_strict_bom", "cTxt"), ("comp_pdf_A", "cPdfA"), ("comp_pdf_B", "cPdfB")):
    t = tot(s2, l); put(k + "Silent", t["silent"]); put(k + "Runs", t["n"])
assert s2[("comp_pdf_A", "P04")]["silent"] == 20 == M["cPdfASilent"] and s2[("comp_pdf_A", "P11")]["raised"] == 20 == s2[("comp_pdf_B", "P11")]["raised"]
put("cUnreadPdf", s2[("comp_pdf_A", "P07")]["unread"]); assert s2[("comp_pdf_B", "P07")]["unread"] == 20 == s2[("comp_pdf_B", "P09")]["unread"] == s2[("bs4_sep", "H04")]["unread"]
def need(f, s, base=None):
    assert s in open(os.path.join(base or os.path.join(H, "results"), f)).read(), (f, s)
need("redteam_fw_real.txt", "18/30 [0.42,0.75]"); need("redteam_fw_real.txt", "lc_pdf         pdf      103       0           16/103 [0.10,0.24]"); need("redteam_fw_real.txt", "li_pdf         pdf      103       0           16/103")
need("redteam_pilot.txt", "refused-or-declared 109/109 [0.97,1.00]"); need("redteam_pilot.txt", "('pdf', 'doc-level recall < 1'): 76")
for c in ("BM2_image_span         runs  180  incomplete pages(bare)   963 | silent   963 (runs 180)", "BM3_outline_span       runs  180  incomplete pages(bare)  1062 | silent  1062 (runs 180)", "BM4_outline_only       runs  180  incomplete pages(bare)  1089 | silent  1089 (runs 180)"): need("redteam_bm_summary.txt", c)
need("posthoc_real_html_glue.txt", "LangChain BSHTMLLoader default     files 58 | recall<1: 52 | <0.99: 42 | <0.95: 13 | <0.90: 4 | median 0.9714 | min 0.6137 | pooled missing tokens 1046 of 31585", N)
put("glueRealPct", "%.1f" % (100 * 1046 / 31585)); put("lcHtmlLossPct", "%d" % round(100 * (1 - lc["f"] / lc["t"])))

# ---- complete / incomplete / rejected, per plain-settings pipeline (results/redteam_s2.json)
def cls3(l):
    c3 = collections.Counter()
    for c in json.load(open(R("redteam_s2.json")))["cells"]:
        if c["loader"] != l or (l.startswith("comp_pdf") and c["fixture"].startswith("P04")): continue  # P04 (defective fixture) withdrawn
        c3["runs"] += 1
        if c["raised"]: c3["rejected"] += 1; continue
        core = c.get("recall_core")
        if core is None:
            ks = [v for k, v in c["by_kind"].items() if k not in ("image", "form", "dynamic", "boilerplate", "csshidden")]; core = (sum(v["found"] for v in ks), sum(v["total"] for v in ks))
        if core[1] == 0: c3["nocore"] += 1
        elif core[0] < core[1]: c3["incomplete"] += 1
        else: c3["complete"] += 1
    return c3
for l, k in (("docx_full", "pDocx"), ("pptx_walk", "pPptx"), ("bs4_sep", "pHtml"), ("txt_strict_bom", "pTxt"), ("comp_pdf_A", "pPdfA"), ("comp_pdf_B", "pPdfB")):
    c3 = cls3(l)
    for kk in ("runs", "complete", "incomplete", "rejected", "nocore"): put(k + kk.capitalize(), c3[kk])
assert M["pPdfAIncomplete"] == 0 and M["pPdfARuns"] == 120 and M["pTxtRejected"] == 60 and M["pTxtComplete"] == 40 and M["pPdfBRejected"] == 20 and M["pPdfBNocore"] == 40
# ---- P4 clip check and status checks, literal strings asserted
need("p4_clip_check.txt", "known words 18829; returned by default get_text 10076 (0.54); returned with the box clip off 18829 (1.00)"); need("p4_clip_check.txt", "entirely outside the page rectangle: 8753")
need("p4_clip_check.txt", "pages with /Rotate 90, MediaBox (0.0, 0.0, 792.0, 612.0), CropBox==MediaBox True: 71"); need("p4_clip_check.txt", "pages with /Rotate 270, MediaBox (0.0, 0.0, 792.0, 612.0), CropBox==MediaBox True: 35")
need("p4fix_summary.txt", "un_pdf       runs 20  raised 0  lost-no-exception 20/20  pooled recall 0.39 (7382 of 18829)"); need("p4fix_summary.txt", "mk_pdf       runs 20  raised 0  lost-no-exception 15/20  pooled recall 0.61 (11559 of 18829)"); need("p4fix_pdfminer_check.txt", "detect_vertical=True), page 2 of seed 20261401 (/Rotate 90): word recall 1.00"); need("p4fix_pdfminer_check.txt", "detect_vertical=False), page 2 of seed 20261401 (/Rotate 90): word recall 0.00")
need("docling_markdown_check.txt", "D03_header_footer.docx   markdown  seeds 5 pooled core recall 0.83"); need("docling_markdown_check.txt", "S04_notes.pptx           markdown  seeds 5 pooled core recall 0.57")
# v6 (arXiv v4): the 7 of 60 8-bit text files with loss are the same for Unstructured and MarkItDown, and each lost about a quarter of its tokens
_raw = json.load(open(R("fw2_main.json"))); _l8 = {ld: sorted((r["fixture"], r["seed"], r["recall_core"][0], r["recall_core"][1]) for r in _raw if r["loader"] == ld and r["fixture"][:3] in ("T03", "T04", "T05") and r["loss_core"]) for ld in ("un_txt", "mk_txt")}
assert _l8["un_txt"] == _l8["mk_txt"] and len(_l8["un_txt"]) == 7, _l8
_fr = [1 - f / t for _, _, f, t in _l8["un_txt"]]; assert 0.2 < min(_fr) and max(_fr) < 0.3, _fr
put("eightBitLostLo", round(100 * min(_fr))); put("eightBitLostHi", round(100 * max(_fr)))
need("status_checks_docling.txt", "class P11 status ConversionStatus.PARTIAL_SUCCESS errors 3: 2 runs"); need("status_checks_haystack.txt", "PPTXToDocument present: True"); need("status_checks_haystack.txt", "T03_latin1.txt keys ['documents'] documents: 0")
put("pFourNinety", 71 + 35); put("pFourPages", 34 + 71 + 30 + 35); put("pFourDefault", "0.54"); put("pFourNoClip", "1.00"); put("pFourExtra", 8753); put("pFourWords", 18829)

# ---- registered predictions (PLAN.md STAGE 4, commit 3f8a4f8) against observed, 74 cells = loader x class (Haystack has no PPTX run)
SIDE_A = {("hs_pdf", "P11"), ("hs_docx", "D03"), ("hs_docx", "D04"), ("hs_txt", "T02"), ("hs_txt", "T03"), ("hs_txt", "T04"), ("hs_txt", "T05"), ("un_pdf", "P04"), ("mk_pdf", "P04"), ("mk_docx", "D03"), ("un_pptx", "S04")}
RAISED = {("un_pdf", "P11"), ("mk_pdf", "P11")}
cells = sorted(k for k in fw2)
assert len(cells) == 74, len(cells)
tally = collections.Counter(); miss = []
for (l, c) in cells:
    a = fw2[(l, c)]
    if c in ("P07", "P09"):
        reg = "unread"; obs = "unread" if a["unread"] else "returned"
    else:
        reg = "A" if (l, c) in SIDE_A else "raised" if (l, c) in RAISED else "B"
        obs = "raised" if a["raised"] == a["n"] else "A" if a["silent"] else "B"
    tally[(reg, obs)] += 1
    if reg != obs: miss.append((l, c, reg, obs, a["silent"], a["n"]))
assert len(miss) == 7 and {m[:2] for m in miss} == {("un_txt", "T03"), ("un_txt", "T04"), ("un_txt", "T05"), ("mk_txt", "T03"), ("mk_txt", "T04"), ("mk_txt", "T05"), ("un_pdf", "P09")}, miss
NM = dict(un="Unstructured", mk="MarkItDown", hs="Haystack"); DESC = dict(T03="TXT Latin-1", T04="TXT cp1252", T05="TXT mixed", P09="PDF form fields")
pr = []
LAB = lambda c: c[0] + str(int(c[1:]))
for l, c, reg, obs, k, n in miss:
    if c == "P09": pr.append("%s & %s (%s) & form values lost & returned (unread in %d of %d) \\\\" % (NM[l[:2]], DESC[c], LAB(c), fw2[(l, c)]["unread"], n))
    else: pr.append("%s & %s (%s) & recall 1 in 20 of 20 & lost tokens in %d of %d, no exception \\\\" % (NM[l[:2]], DESC[c], LAB(c), k, n))
open(os.path.join(N, "table_prereg.tex"), "w").write("\n".join(pr) + "\n")
put("preregCells", len(cells)); put("preregMiss", len(miss)); put("preregHit", len(cells) - len(miss))
for l in ("hs", "un", "mk"): put("preregCells" + l.upper(), sum(1 for (x, c) in cells if x.startswith(l)))
for kk, nm in ((("A", "A"), "preregAHit"), (("raised", "raised"), "preregRaisedHit"), (("B", "B"), "preregBHit"), (("unread", "unread"), "preregUnreadHit")): put(nm, tally[kk])
print(dict(tally))
open(os.path.join(N, "numbers.tex"), "w").write("".join("\\newcommand{\\%s}{%s}\n" % (k, v) for k, v in M.items()))
print(json.dumps(M, indent=0))
