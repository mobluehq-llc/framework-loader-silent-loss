"""Summary of results/p4fix.json (AMENDMENT 5). usage: python3 stage3/p4fix_sum.py > results/p4fix_summary.txt"""
import json, collections, os
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); A = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
for c in json.load(open(os.path.join(H, "results", "p4fix.json"))):
    a = A[c["loader"]]; a[0] += 1
    if c["raised"]: a[1] += 1; continue
    f, t = c["recall_core"]; a[2] += f; a[3] += t; a[4] += f < t
for k in ("lc_pdf", "li_pdf", "docling_pdf", "hs_pdf", "un_pdf", "mk_pdf", "pymupdf"):
    a = A[k]; print("P04 corrected  %-12s runs %2d  raised %d  lost-no-exception %2d/%d  pooled recall %.2f (%d of %d)" % (k, a[0], a[1], a[4], a[0], a[2] / a[3], a[2], a[3]))
