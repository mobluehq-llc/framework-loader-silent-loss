"""usage: analyze2.py results.json [--tables]  -> instrument checks, Q1 rates with Wilson CIs, pooled recall with cluster bootstrap, remedy bars."""
import json, sys, collections, math, random
R = json.load(open(sys.argv[1])); C = R["cells"]; M = [c for c in C if c.get("measured")]
CORE = {"text", "hidden", "body", "table", "header", "footer", "group", "notes", "entity"}
CTRL = {"pdf": "P01_text", "docx": "D01_body", "pptx": "S01_textboxes", "html": "H01_body", "txt": "T01_utf8"}
def wilson(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z * z / n; ce = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return (max(0, ce - h), min(1, ce + h))
seeds = sorted({c["seed"] for c in C}); K = len(seeds)
print("seeds", K, "cells", len(C), "not measured", [(c["seed"], c["fixture"], c["loader"], c.get("why")) for c in C if not c.get("measured")][:5])
rc = R["refcheck"]; bad = [r for r in rc if r.get("equal") is False]
print("CHECK (c) reference vs truth: equal %d, not equal %d, undecodable-by-design %d" % (sum(r.get("equal") is True for r in rc), len(bad), sum(r.get("equal") is None for r in rc)), [(r["seed"], r["fixture"], r["ref_only"], r["truth_only"]) for r in bad][:8])
pos = {}
for fmt, f in CTRL.items():
    for s in seeds: pos[(fmt, s)] = any(not c["loss_any"] for c in M if c["seed"] == s and c["fixture"] == f and c["loader"] != "stub_empty")
print("CHECK (a) positive control: replicates with some perfect loader, by format:", {fmt: sum(pos[(fmt, s)] for s in seeds) for fmt in CTRL}, "of", K)
stub = [c for c in M if c["loader"] == "stub_empty"]
print("CHECK (b) negative control: stub flagged silent_core on", sum(c["silent_core"] for c in stub), "of", len(stub))
print("\nQ1: silent CORE loss, count/K [95% Wilson]; U=silent expected-unreadable loss (image/form/dynamic), S=silent selective loss (boilerplate/css-hidden); loud = L")
tab = collections.defaultdict(list)
for c in M:
    if c["loader"] != "stub_empty": tab[(c["fixture"], c["loader"])].append(c)
fam = collections.defaultdict(lambda: collections.defaultdict(list))
for (f, l), cs in sorted(tab.items()):
    k = sum(c["silent_core"] for c in cs); n = len(cs); lo, hi = wilson(k, n); ku = sum(c["silent_unread"] for c in cs); ks = sum(c["silent_sel"] for c in cs); kl = sum(c["loud"] for c in cs)
    if k or ku or ks or kl: print("  %-22s %-16s core %2d/%d [%.2f,%.2f]  U %2d  S %2d  loud %2d" % (f, l, k, n, lo, hi, ku, ks, kl))
    if k: fam[cs[0]["family"]][(f, l)].append((k, n, lo))
print("\nfamilies with silent CORE loss (class, loader, k/n, Wilson lower bound>0):")
for fm, d in sorted(fam.items()): print("  ", fm, [(f, l, "%d/%d" % (v[0][0], v[0][1])) for (f, l), v in sorted(d.items())])
print("n families with silent core loss:", len(fam))
print("\nPOOLED CORE word recall per loader (cluster bootstrap over replicates, 95%):")
rng = random.Random(1)
for fmt in CTRL:
    for l in sorted({c["loader"] for c in M if c["fmt"] == fmt and c["loader"] != "stub_empty"}):
        by = collections.defaultdict(lambda: [0.0, 0])
        for c in M:
            if c["loader"] == l and c["fmt"] == fmt:
                for k, v in c["by_kind"].items():
                    if k in CORE: by[c["seed"]][0] += v["found"]; by[c["seed"]][1] += v["total"]
        ss = list(by); f = sum(by[s][0] for s in ss) / max(1, sum(by[s][1] for s in ss)); bs = []
        for _ in range(2000):
            pick = [rng.choice(ss) for _ in ss]; bs.append(sum(by[s][0] for s in pick) / max(1, sum(by[s][1] for s in pick)))
        bs.sort(); print("  %-5s %-18s %.3f [%.3f,%.3f]" % (fmt, l, f, bs[50], bs[1949]))
print("\nREMEDY bars")
for k in ("R", "M1", "M2", "M3"):
    W = [(c, c["wrap"][k]) for c in M if c["loader"] != "stub_empty"]
    sd = sum(w["silent_drops"] for c, w in W); cells = sum(w["silent_drops"] > 0 for c, w in W); ref = sum(w["loud"] is not None for c, w in W)
    faults = [(c["fixture"], c["loader"], w["loud"]) for c, w in W if w["loud"] and "AccountantFault" in str(w["loud"])]
    fa = [(c["seed"], c["fixture"], c["loader"]) for c, w in W if w["loud"] and "ConservationError" in str(w["loud"]) and not c["loss_any"]]
    fac = [x for x in fa if x[1] in CTRL.values()]
    where = collections.Counter((c["fixture"]) for c, w in W if w["silent_drops"] > 0)
    print(k, "silent_drop_units", sd, "| cells", cells, "| wrapper refusals", ref, "| false alarms (all/controls)", len(fa), len(fac), "| accountant faults", len(faults), faults[:2], "| silent drops by class", dict(where))
print("\nBare loader totals: silent_core %d, loud-with-loss %d, no loss %d (cells %d)" % (sum(c["silent_core"] for c in M if c["loader"] != "stub_empty"), sum(c["loud"] and c["loss_any"] for c in M if c["loader"] != "stub_empty"), sum(not c["loss_any"] for c in M if c["loader"] != "stub_empty"), len([c for c in M if c["loader"] != "stub_empty"])))
print("page_count_error/misnumbered nonzero cells:", sum(c["page_count_error"] != 0 or c["misnumbered"] > 0 for c in M))
