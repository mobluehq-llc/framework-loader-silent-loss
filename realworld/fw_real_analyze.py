"""M4 on real files: framework default loaders vs reference (PDF: pypdfium2 tokens; HTML/TXT: registered fullest idiom). usage: .venv/bin/python -I realworld/fw_real_analyze.py"""
import os, sys, json, glob, collections, math
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(H), "stage3"))
from conserve2 import toks, recall
import loaders3 as L
def wil(k, n, z=1.96):
    if not n: return (0, 0)
    p = k / n; d = 1 + z * z / n; ce = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return max(0, ce - h), min(1, ce + h)
by = collections.defaultdict(dict)
for f in glob.glob(os.path.join(H, "work", "cells", "*.json")):
    c = json.load(open(f)); by[c["path"]][c["loader"]] = c
fw = collections.defaultdict(dict)
for f in glob.glob(os.path.join(H, "work", "fw", "*.json")):
    c = json.load(open(f)); fw[c["loader"]][c["path"]] = c
print("%-14s %-6s %5s %7s %22s %22s  reference" % ("framework", "fmt", "files", "raised", "recall<0.90 [Wilson]", "recall<0.50"))
for fid, d in sorted(fw.items()):
    res = []; rz = 0
    for p, c in d.items():
        cells = by.get(p, {}); fmt = c["fmt"]
        if fmt == "pdf":
            ref = cells.get("pypdfium2")
            if not ref or ref["raised"]: continue
            R = toks("\n".join(ref["pages"]))
        else:
            ok = [l for l in L.L2.IDS[fmt] if l in cells and not cells[l]["raised"]]
            if not ok: continue
            T = {l: toks("\n".join(cells[l]["pages"])) for l in ok}; full = max(ok, key=lambda l: (sum(T[l].values()), -L.L2.IDS[fmt].index(l))); R = T[full]
        if sum(R.values()) < 50: continue
        if c["raised"]: rz += 1; continue
        res.append(recall(R, collections.Counter(c["tokens"])))
    k9 = sum(x < .9 for x in res); k5 = sum(x < .5 for x in res)
    print("%-14s %-6s %5d %7d %12d/%d [%.2f,%.2f] %9d/%d [%.2f,%.2f]  %s" % (fid, next(iter(d.values()))["fmt"], len(res), rz, k9, len(res), *wil(k9, len(res)), k5, len(res), *wil(k5, len(res)), "pypdfium2" if fid.endswith("pdf") else "fullest idiom"))
