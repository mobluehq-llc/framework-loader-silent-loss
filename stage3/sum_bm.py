"""Summarise run_bm.py output. usage: python -I stage3/sum_bm.py OUT.json"""
import json, sys, collections
R = json.load(open(sys.argv[1])); print("runs", len(R), "seeds", len({r["seed"] for r in R}))
cls = sorted({r["cls"] for r in R})
for w in ("W", "W2", "Wdual"):
    print("\n==", w, ": per class: accepted-but-incomplete pages (silent) / runs returned; refusals; declared_unreadable pages; declared_unreadable on truth-empty pages")
    for c in cls:
        rs = [r for r in R if r["cls"] == c and not r["raised"]]
        sil = sum(r[w].get("silent", 0) for r in rs if w in r); ref = sum("refused" in r[w] for r in rs if w in r); du = sum(r[w].get("declared_unreadable", 0) for r in rs if w in r); fault = sum("fault" in r[w] for r in rs if w in r)
        due = sum(r[w].get("declared_unreadable_when_truth_empty", 0) for r in rs if w in r)
        inc = sum(r["incomplete_pages"] for r in rs); runs_sil = sum(1 for r in rs if w in r and r[w].get("silent", 0) > 0)
        print("  %-22s runs %4d  incomplete pages(bare) %5d | silent %5d (runs %3d) refused %4d declUnread %5d declUnread-on-empty %4d faults %d" % (c, len(rs), inc, sil, runs_sil, ref, du, due, fault))
print("\nloader raised by class:", dict(collections.Counter((r["cls"]) for r in R if r["raised"])))
print("Wdual refusal reasons:", collections.Counter((r["cls"], r["Wdual"]["refused"]) for r in R if "Wdual" in r and "refused" in r["Wdual"]).most_common(8))
print("W2 silent by loader on BM1-5:", dict(collections.Counter(r["loader"] for r in R if r["cls"].startswith("BM") and "W2" in r and r["W2"].get("silent", 0) > 0)))
