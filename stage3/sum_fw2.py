import json, sys, collections
R = json.load(open(sys.argv[1])); print("records", len(R), "seeds", len({r["seed"] for r in R}))
print("%-8s %-22s %3s %6s %6s %7s %6s  recall_core_min  logged" % ("loader", "class", "n", "raised", "silent", "unread", "recall"))
for l in sorted({r["loader"] for r in R}):
    for fx in sorted({r["fixture"] for r in R if r["loader"] == l}):
        g = [r for r in R if r["loader"] == l and r["fixture"] == fx]
        rz = sum(r["raised"] for r in g); lo = sum((not r["raised"]) and r["loss_core"] for r in g); lu = sum((not r["raised"]) and r["loss_unread"] for r in g)
        f = sum(r["recall_core"][0] for r in g if not r["raised"]); t = sum(r["recall_core"][1] for r in g if not r["raised"])
        lg = sum(1 for r in g if r["logged_warnings"])
        print("%-8s %-22s %3d %6d %6d %7d %6s  logged_in=%d exc=%s" % (l, fx, len(g), rz, lo, lu, ("%.3f" % (f / t)) if t else "--", lg, {r["exc"][:50] for r in g if r["raised"]} or ""))
