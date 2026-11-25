"""S3 pilot, step 2: M1 W refusal rate (+ 'likely false' proxy), M2 idiom divergence vs fullest idiom, M3 dual-engine page flags.
usage: .venv/bin/python -I realworld/pilot_analyze.py > results/redteam_pilot.txt"""
import os, sys, json, glob, csv, collections, math
H = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(H); sys.path.insert(0, os.path.join(ROOT, "stage3"))
from conserve2 import account, ConservationError, toks, recall
import loaders3 as L
def wil(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n; d = 1 + z * z / n; ce = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return max(0, ce - h), min(1, ce + h)
fmt_s = lambda k, n: "%d/%d [%.2f,%.2f]" % (k, n, *wil(k, n))
cells = [json.load(open(f)) for f in glob.glob(os.path.join(H, "work", "cells", "*.json"))]
by = collections.defaultdict(dict)
for c in cells: by[c["path"]][c["loader"]] = c
IDS = L.L2.IDS; DG = {"markitdown_pdf"}
src = {}
for tsv, pre in (("MANIFEST_fetch.tsv", None), ("MANIFEST_gov.tsv", "gov")):
    if os.path.exists(os.path.join(H, tsv)):
        for r in csv.DictReader(open(os.path.join(H, tsv)), delimiter="\t"):
            pth = os.path.join(H, "raw", "gov", r["kind"], r["file"]) if pre else os.path.join(H, "raw", r["kind"], r["file"]); src[pth] = ("govdocs1" if pre else r["kind"]) 
print("files with cells:", len(by), " by source:", dict(collections.Counter(src.get(p, "?") for p in by)), " by format:", dict(collections.Counter(next(iter(d.values()))["fmt"] for d in by.values())))
def tk(c): return toks("\n".join(c["pages"])) if not c["raised"] else None
GROUP = {"txt_utf8_ignore": "A", "txt_utf8_replace": "A", "txt_latin1": "A", "bs4_text": "A", "lxml_text": "A"}
res = collections.defaultdict(list)  # (fmt, loader) -> list of dict
M1 = collections.defaultdict(collections.Counter); noext = collections.Counter(); nfiles = collections.Counter(); wreasons = collections.Counter()
for p, d in sorted(by.items()):
    fmt = next(iter(d.values()))["fmt"]; nfiles[fmt] += 1
    T = {l: tk(c) for l, c in d.items()}; ok = [l for l in IDS[fmt] if l in T and T[l] is not None]
    if not ok: noext[fmt, "no loader returned"] += 1; continue
    full = max(ok, key=lambda l: (sum(T[l].values()), -IDS[fmt].index(l)));
    ftot = sum(T[full].values())
    if ftot == 0: noext[fmt, "fullest idiom returned zero tokens (no extractable text by any idiom)"] += 1; continue
    for l in IDS[fmt]:
        if l not in d: continue
        c = d[l]; r = dict(file=p, raised=c["raised"], stderr=c["stderr_bytes"] > 0, full=full, fulltot=ftot)
        if not c["raised"]:
            rc = recall(T[full], T[l]); r["recall"] = rc
        # wrapper verdict
        if c["raised"]: r["w"] = "loader_raised"
        else:
            try:
                a = account(p, fmt, l, dict(raised=False, pages=c["pages"]), None, DG); r["w"] = "declared_unreadable" if "declared_unreadable" in a["units"] else "accept"
            except ConservationError as e: r["w"] = "refused"; wreasons[(fmt, str(e).split(":")[0][:40] if "page recall" not in str(e) else "page recall <1")] += 1
            except Exception as e: r["w"] = "fault"; wreasons[(fmt, "FAULT " + type(e).__name__)] += 1
        # M1 proxy: engines agree
        pairs = {"pdf": ("pypdfium2", "pymupdf"), "html": ("bs4_sep", "lxml_text"), "txt": ("txt_utf8_strict", "txt_charset_normalizer")}[fmt]
        if all(x in T and T[x] is not None for x in pairs):
            A, B = T[pairs[0]], T[pairs[1]]; r["agree"] = min(recall(A, B), recall(B, A)) >= 0.95
        else: r["agree"] = False
        res[(fmt, l)].append(r)
print("\nfiles by format:", dict(nfiles), "| files where no usable text:", dict(noext))
print("\n=== M2 idiom divergence vs fullest idiom (returned without exception). D90: token recall of fullest < 0.90; D50 < 0.50. n = files with extractable text where the idiom did not raise; raise% separately")
print("%-5s %-24s %4s %6s %26s %26s %9s %9s" % ("fmt", "idiom", "n", "raise", "D90 [95% Wilson]", "D50 [95% Wilson]", "stderr%", "mean rec"))
for (fmt, l), rs in sorted(res.items(), key=lambda x: (x[0][0], IDS[x[0][0]].index(x[0][1]))):
    nr = [r for r in rs if not r["raised"]]; n = len(nr); k90 = sum(r["recall"] < 0.90 for r in nr); k50 = sum(r["recall"] < 0.50 for r in nr)
    print("%-5s %-24s %4d %5.0f%% %26s %26s %8.0f%% %9.3f" % (fmt, l + ("[" + GROUP[l] + "]" if l in GROUP else ""), n, 100 * (len(rs) - n) / len(rs), fmt_s(k90, n), fmt_s(k50, n), 100 * sum(r["stderr"] for r in nr) / max(1, n), sum(r["recall"] for r in nr) / max(1, n)))
print("\n=== M1 wrapper W verdicts on real files (all idioms; unit = file x idiom). Likely-false = refused/declared_unreadable while two engines agree (mutual recall>=0.95).")
print("%-5s %-24s %4s | %7s %8s %8s %8s %6s | %s" % ("fmt", "idiom", "n", "accept", "decl_unr", "refused", "raised", "fault", "likely-false among refused+declared"))
for (fmt, l), rs in sorted(res.items(), key=lambda x: (x[0][0], IDS[x[0][0]].index(x[0][1]))):
    c = collections.Counter(r["w"] for r in rs); nonacc = [r for r in rs if r["w"] in ("refused", "declared_unreadable")]
    print("%-5s %-24s %4d | %7d %8d %8d %8d %6d | %d/%d" % (fmt, l, len(rs), c["accept"], c["declared_unreadable"], c["refused"], c["loader_raised"], c["fault"], sum(r["agree"] for r in nonacc), len(nonacc)))
print("\nW refusal reasons:", dict(wreasons))
# fullest-idiom summary per format
print("\n=== M1 headline per format, FULLEST idiom of each file: refusal+declared rate")
for fmt in ("pdf", "html", "txt"):
    rs = [r for (f, l), g in res.items() if f == fmt for r in g if r["full"] == l]
    n = len(rs); c = collections.Counter(r["w"] for r in rs); na = c["refused"] + c["declared_unreadable"]
    print(fmt, "files", n, dict(c), "refused-or-declared", fmt_s(na, n), " likely-false", sum(r["agree"] for r in rs if r["w"] in ("refused", "declared_unreadable")), "/", na)
# M3 dual engine
print("\n=== M3 dual-engine PDF (pypdfium2 vs pymupdf, per page mutual token recall < 0.9 flagged)")
pages = fl = blank = 0; files = ffl = fmis = 0; flagged_files = []
for p, d in by.items():
    if next(iter(d.values()))["fmt"] != "pdf": continue
    a, b = d.get("pypdfium2"), d.get("pymupdf")
    if not a or not b or a["raised"] or b["raised"]: continue
    files += 1
    if len(a["pages"]) != len(b["pages"]): fmis += 1; continue
    ff = False
    for x, y in zip(a["pages"], b["pages"]):
        X, Y = toks(x), toks(y)
        if not X and not Y: blank += 1; continue
        pages += 1
        if min(recall(X, Y), recall(Y, X)) < 0.9: fl += 1; ff = True
    ffl += ff
    if ff: flagged_files.append(os.path.basename(p))
print("files with both engines returning:", files, "page-count mismatch:", fmis, "| pages with text in either:", pages, "flagged", fmt_s(fl, pages), "| blank (both empty):", blank, "| files with >=1 flagged page", fmt_s(ffl, files - fmis))
print("flagged files (first 10):", flagged_files[:10])
raisedp = collections.Counter((c["fmt"], c["loader"]) for c in cells if c["raised"]); print("\nloader raised counts:", dict(raisedp))
