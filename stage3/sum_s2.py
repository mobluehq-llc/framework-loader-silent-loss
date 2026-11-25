"""Summarise S2 (competent baseline) paired by seed,fixture. usage: python -I stage3/sum_s2.py results/redteam_s2.json"""
import json, sys, collections, math
D = json.load(open(sys.argv[1])); C = [c for c in D["cells"] if c.get("measured") and c["loader"] != "stub_empty"]
print("cells", len(D["cells"]), "bare", len(C), "unmeasured", sum(not c.get("measured") for c in D["cells"]))
def wil(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z * z / n; ce = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return max(0, ce - h), min(1, ce + h)
print("%-8s %-24s %5s | C: silent_core loud loss-any(loud) silent_unread | C+W: silent drops(units) refused-of-C-complete refused-of-C-lossy declared_unread" % ("fmt", "pipeline/class", "runs"))
tot = collections.Counter()
for lid in sorted({c["loader"] for c in C}):
    for fx in sorted({c["fixture"] for c in C if c["loader"] == lid}):
        g = [c for c in C if c["loader"] == lid and c["fixture"] == fx]
        sc = sum(c["silent_core"] for c in g); su = sum(c["silent_unread"] for c in g); lo = sum(c["loud"] for c in g); la = sum(c["loud"] and c["loss_any"] for c in g)
        wd = sum(c["wrap"]["R"]["silent_drops"] for c in g); ref = lambda c: c["wrap"]["R"]["loud"] is not None and not c["raised"]
        rf_c = sum(ref(c) and not c["loss_any"] for c in g); rf_l = sum(ref(c) and c["loss_any"] for c in g); du = sum("declared_unreadable" in c["wrap"]["R"]["statuses"] for c in g)
        for k, v in (("silent_core", sc), ("silent_unread", su), ("w_drops", wd), ("w_refuse_complete", rf_c), ("w_refuse_lossy", rf_l), ("runs", len(g))): tot[(lid, k)] += v
        if sc or su or wd or rf_c or rf_l or lo: print("%-8s %-30s %3d | %2d %2d %2d %2d | %2d %2d %2d %2d" % (g[0]["fmt"], lid + "/" + fx.split("_")[0], len(g), sc, lo, la, su, wd, rf_c, rf_l, du))
print("\nTOTALS per pipeline (runs; silent core loss under C; W silent drops on top; W refusals of C-complete runs; W refusals of C-lossy (non-raised) runs)")
for lid in sorted({c["loader"] for c in C}):
    n = tot[(lid, "runs")]; print("  %-16s runs %3d silent_core %3d (seed-level wilson upper %.2f) silent_unread %3d | W drops %d | W refuse complete %d | W refuse lossy %d" % (lid, n, tot[(lid, "silent_core")], wil(sum(1 for s in {c["seed"] for c in C if c["loader"] == lid} if any(c["silent_core"] for c in C if c["loader"] == lid and c["seed"] == s)), len({c["seed"] for c in C}))[1], tot[(lid, "silent_unread")], tot[(lid, "w_drops")], tot[(lid, "w_refuse_complete")], tot[(lid, "w_refuse_lossy")]))
print("\nclasses where competent pipeline still silently loses core text:", sorted({(c["loader"], c["fixture"].split("_")[0]) for c in C if c["silent_core"]}))
