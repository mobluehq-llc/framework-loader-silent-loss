"""AG v16 (ChatGPT R2 blocker 1): the two-reader comparison ALONE on the constructed both-miss PDFs.
Reader pair and rule as M3 on real PDFs (realworld/pilot_analyze.py): pypdfium2 vs PyMuPDF per page,
page flagged when min(recall(a,b), recall(b,a)) < 0.90; pages empty in both readers are not flagged.
No truncation, structure, ink-flag or page-recall test (those belong to the broader wrapper Wdual).
Run-level join: results/redteam_bm_all.json gives, per (seed, class, loader) run, incomplete_pages.
A run counts as 'accepted incomplete' when it has >=1 incomplete page and the two-reader comparison
flags no page of that file. usage: python -I stage3/two_reader_only_bm.py BM_RUNS.json FIXDIR [FIXDIR...]"""
import sys, os, json, glob, collections, re, hashlib
TOK = re.compile(r"[a-z0-9]+")
def toks(s): return collections.Counter(TOK.findall(s.lower()))
def recall(R, O):
    n = sum(R.values()); return 1.0 if n == 0 else sum(min(v, O[k]) for k, v in R.items()) / n
import pymupdf, pypdfium2
runs = json.load(open(sys.argv[1])); files = {}
for fix in sys.argv[2:]:
    for p in sorted(glob.glob(os.path.join(fix, "*", "bm", "BM[234]_*.pdf"))):
        seed = p.split(os.sep)[-3]; cls = json.load(open(p + ".json"))["id"]
        d = pypdfium2.PdfDocument(p); a = [toks(d[i].get_textpage().get_text_range()) for i in range(len(d))]; d.close()
        m = pymupdf.open(p); b = [toks(pg.get_text()) for pg in m]; m.close()
        man = json.load(open(p + ".json")); truth = [toks(" ".join(u["A"] + u["B"])) for u in man["units"]]
        fl = blank = refmiss = 0
        for i in range(len(truth)):
            X, Y = a[i], b[i]
            if not X and not Y: blank += 1
            elif min(recall(X, Y), recall(Y, X)) < 0.90: fl += 1
            U = X | Y
            if recall(truth[i], U) < 1.0: refmiss += 1
        files[(seed, cls)] = dict(pages=len(truth), flagged=fl, both_empty=blank, pages_both_readers_incomplete=refmiss, sha256=hashlib.sha256(open(p, "rb").read()).hexdigest()[:16])
print("pymupdf", pymupdf.__version__, "pypdfium2", pypdfium2.V_PYPDFIUM2 if hasattr(pypdfium2, "V_PYPDFIUM2") else "?")
print("files", len(files), "seeds", len({s for s, _ in files}))
for c in ("BM2_image_span", "BM3_outline_span", "BM4_outline_only"):
    F = {k: v for k, v in files.items() if k[1] == c}
    R = [r for r in runs if r["cls"] == c and not r["raised"]]
    inc = [r for r in R if r["incomplete_pages"] > 0]
    acc = [r for r in inc if files[(r["seed"], c)]["flagged"] == 0]
    print("\n%s files %d pages %d flagged-pages %d both-empty-pages %d pages-both-readers-incomplete %d" % (c, len(F), sum(v["pages"] for v in F.values()), sum(v["flagged"] for v in F.values()), sum(v["both_empty"] for v in F.values()), sum(v["pages_both_readers_incomplete"] for v in F.values())))
    print("  loader runs %d | runs with an incomplete page %d | of those, accepted by the two-reader comparison alone (no page of the file flagged) %d" % (len(R), len(inc), len(acc)))
mix = [r for r in runs if r["cls"] in ("BM2_image_span", "BM3_outline_span") and not r["raised"] and r["incomplete_pages"] > 0]
print("\nMIXED (BM2+BM3): accepted %d of %d runs with an incomplete page" % (sum(files[(r["seed"], r["cls"])]["flagged"] == 0 for r in mix), len(mix)))
json.dump({"%s/%s" % k: v for k, v in files.items()}, open(os.environ.get("TWO_READER_OUT", "/dev/null"), "w"), indent=0)
