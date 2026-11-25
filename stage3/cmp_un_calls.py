"""Compare Unstructured rows of two runs record by record (raised, loss_core, loss_unread, recall_core, recall_by_kind).
usage: python -I stage3/cmp_un_calls.py REF.json NAME_A A1.json[,A2.json] [NAME_B B1.json[,B2.json] ...]"""
import sys, json, collections
F = ["raised", "loss_core", "loss_unread", "recall_core", "recall_by_kind"]
def ld(spec): return {(r["seed"], r["fixture"], r["loader"]): r for f in spec.split(",") for r in json.load(open(f)) if r["loader"].startswith("un_")}
ref = ld(sys.argv[1]); print("reference", sys.argv[1], "un_* records", len(ref))
a = sys.argv[2:]
for name, spec in zip(a[::2], a[1::2]):
    x = ld(spec); same = set(x) == set(ref); d = [k for k in ref if k in x and any(ref[k].get(f) != x[k].get(f) for f in F)]
    print("\n%s: records %d, same keys %s, records differing in any scored field %d" % (name, len(x), same, len(d)))
    c = collections.Counter((k[1], k[2], tuple(f for f in F if ref[k].get(f) != x[k].get(f))) for k in d)
    for (fx, l, fs), n in sorted(c.items()): print("   %-22s %-8s %3d  differs in %s" % (fx, l, n, ",".join(fs)))
    for k in d[:3]: print("   e.g.", k, {f: (ref[k].get(f), x[k].get(f)) for f in F if ref[k].get(f) != x[k].get(f)}, x[k].get("exc"))
    by = collections.defaultdict(lambda: [0, 0, 0])
    for k, r in x.items(): b = by[(r["loader"], r["fixture"])]; b[0] += 1; b[1] += bool(r.get("raised")); b[2] += bool(r.get("loss_core"))
    print("   per class (n raised lost-core-no-exception):", "; ".join("%s %s %d/%d/%d" % (l, fx, *v) for (l, fx), v in sorted(by.items()) if v[1] or v[2]))
