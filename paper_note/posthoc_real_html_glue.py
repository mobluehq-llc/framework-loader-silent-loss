"""POST-HOC (not registered), for the AG note. From STORED real-file outputs only (realworld/work/cells, realworld/work/fw):
per real HTML file, exact-token recall of the separator idiom's tokens (bs4 get_text(" ")) inside (a) the stored LangChain
BSHTMLLoader default output and (b) the stored bs4 get_text() output. A token missing here was present when blocks were
separated and absent when they were not. usage: python3 paper_note/posthoc_real_html_glue.py > paper_note/posthoc_real_html_glue.txt"""
import os, sys, json, glob, collections, statistics
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, os.path.join(H, "stage3"))
from conserve2 import toks, recall
by = collections.defaultdict(dict)
for f in glob.glob(os.path.join(H, "realworld", "work", "cells", "*.json")):
    c = json.load(open(f)); by[c["path"]][c["loader"]] = c
fw = {}
for f in glob.glob(os.path.join(H, "realworld", "work", "fw", "*.json")):
    c = json.load(open(f))
    if c["loader"] == "lc_html" and not c["raised"]: fw[c["path"]] = collections.Counter(c["tokens"])
def rep(name, pairs):
    r = [recall(R, O) for R, O in pairs if sum(R.values()) >= 50]; n = len(r)
    print("%-34s files %d | recall<1: %d | <0.99: %d | <0.95: %d | <0.90: %d | median %.4f | min %.4f | pooled missing tokens %d of %d" % (
        name, n, sum(x < 1 for x in r), sum(x < .99 for x in r), sum(x < .95 for x in r), sum(x < .90 for x in r), statistics.median(r), min(r),
        sum(sum(max(0, v - O[k]) for k, v in R.items()) for R, O in pairs if sum(R.values()) >= 50), sum(sum(R.values()) for R, O in pairs if sum(R.values()) >= 50)))
A, B = [], []
for p, cells in sorted(by.items()):
    s = cells.get("bs4_sep"); t = cells.get("bs4_text")
    if not s or s["raised"]: continue
    R = toks("\n".join(s["pages"]))
    if p in fw: A.append((R, fw[p]))
    if t and not t["raised"]: B.append((R, toks("\n".join(t["pages"]))))
print("reference = stored bs4 get_text(' ') tokens of the same file; files with >= 50 reference tokens")
rep("LangChain BSHTMLLoader default", A); rep("bs4 get_text() (no separator)", B)
