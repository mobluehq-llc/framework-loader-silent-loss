"""(d) paired-unit reconciliation of A1 (M1), R, A2 (M2) refusals/returns, per run (seed,fixture,loader). usage: .venv/bin/python -I redteam/reconcile_a2.py"""
# NOTE: "M2" here is a test-variant name only (no other meaning).
import json, os, collections
RS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
for tag, f in (("MAIN2", "main2.json"), ("HOLDOUT2", "holdout2.json")):
    B = [c for c in json.load(open(os.path.join(RS, f)))["cells"] if c.get("measured") and c["loader"] != "stub_empty"]
    print("==", tag, len(B))
    for k in ("M1", "M2", "M3", "R"):
        print(k, "non-returns:", sum(c["wrap"][k]["loud"] is not None for c in B))
    m2 = [c for c in B if c["wrap"]["M2"]["loud"] is not None]
    print("M2 non-return reasons:")
    cnt = collections.Counter()
    for c in m2:
        w = c["wrap"]["M2"]["loud"]; cl = "loader raised" if c["raised"] else w.split(":")[1].strip()[:40] if "ConservationError" in w else w[:40]
        cnt[(c["fmt"], c["fixture"].split("_")[0], cl)] += 1
    for k, v in sorted(cnt.items()): print("  ", k, v)
    # which M2 non-returns are not loader-raised
    nr = [c for c in m2 if not c["raised"]]
    print("M2 non-return not due to loader raise:", len(nr), " loader raised:", len(m2) - len(nr))
    # paired: A1-silent lossy runs (silent drop units under M1) -> what happens under R and M2
    lossy = [c for c in B if c["wrap"]["M1"]["silent_drops"] > 0]
    print("A1 lossy runs (M1 silent drops>0):", len(lossy), "units", sum(c["wrap"]["M1"]["silent_drops"] for c in lossy))
    t = collections.Counter()
    for c in lossy:
        r = "R:refuse" if c["wrap"]["R"]["loud"] else ("R:accept-declared" if c["wrap"]["R"]["silent_drops"] == 0 else "R:silent")
        m = "M2:refuse" if c["wrap"]["M2"]["loud"] else ("M2:silent" if c["wrap"]["M2"]["silent_drops"] else "M2:ok")
        t[(r, m)] += 1
    for k, v in sorted(t.items()): print("   lossy run:", k, v)
    u1 = sum(c["wrap"]["M1"]["silent_drops"] for c in B); u2 = sum(c["wrap"]["M2"]["silent_drops"] for c in B)
    surv = [c for c in B if c["wrap"]["M2"]["silent_drops"] > 0]
    print("units M1", u1, "M2", u2, "ratio %.3f" % (u2 / u1), "; runs with M2 silent drops", len(surv), "all also lossy under M1:", all(c["wrap"]["M1"]["silent_drops"] > 0 for c in surv))
    # paired unit survival: per run, min(M1,M2)==M2?
    print("  runs where M2 units > M1 units:", sum(c["wrap"]["M2"]["silent_drops"] > c["wrap"]["M1"]["silent_drops"] for c in B))
    print("  M2 survivors by class:", dict(collections.Counter(c["fixture"].split("_")[0] for c in surv)))
    # P11 runs under A1 vs units
    p11 = [c for c in B if c["fixture"].startswith("P11") and not c["raised"]]
    print("  P11 non-raising runs", len(p11), "R refused:", sum(c["wrap"]["R"]["loud"] is not None for c in p11), "M2 refused:", sum(c["wrap"]["M2"]["loud"] is not None for c in p11))
    # P11 page-id detail
    for c in p11[:0]: pass
