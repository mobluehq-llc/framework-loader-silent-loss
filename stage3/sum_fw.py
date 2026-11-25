import json, sys, collections
R = json.load(open(sys.argv[1])); print("records", len(R), "seeds", len({r["seed"] for r in R}))
print("%-14s %-22s %3s %6s %5s  (core loss without exception / seeds)" % ("framework", "class", "n", "raised", "loss"))
for l in sorted({r["loader"] for r in R}):
    for fx in sorted({r["fixture"] for r in R if r["loader"] == l}):
        g = [r for r in R if r["loader"] == l and r["fixture"] == fx]; rz = sum(r["raised"] for r in g); lo = sum((not r["raised"]) and r["loss_core"] for r in g); lu = sum((not r["raised"]) and r.get("loss_unread") for r in g)
        if rz or lo or lu: print("%-14s %-22s %3d %6d %5d unread-loss %d  exc=%s" % (l, fx, len(g), rz, lo, lu, {r["exc"][:60] for r in g if r["raised"]} or ""))
print("\nper framework totals: runs, raised, silent core loss, classes with silent core loss")
for l in sorted({r["loader"] for r in R}):
    g = [r for r in R if r["loader"] == l]; print("  %-14s runs %3d raised %3d silent_core %3d classes %s" % (l, len(g), sum(r["raised"] for r in g), sum((not r["raised"]) and r["loss_core"] for r in g), sorted({r["fixture"].split("_")[0] for r in g if (not r["raised"]) and r["loss_core"]})))
