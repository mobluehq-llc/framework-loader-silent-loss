"""Item 2: re-cut Q1 into caller-idiom / library-engine / modality-gap groups; recall-when-silent next to loud rate.
usage: .venv/bin/python -I redteam/recut.py > results/redteam_recut.txt"""
import json, collections, os, random, math
RS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
CORE = {"text", "hidden", "body", "table", "header", "footer", "group", "notes", "entity"}
CALLER = {"txt_utf8_ignore", "txt_utf8_replace", "txt_latin1", "bs4_text", "lxml_text", "docx_paragraphs", "pptx_shapes"}
def grp(l, fx):
    if l in CALLER: return "A caller-idiom footgun"
    return "B library/engine behaviour"
def wil(k, n, z=1.96):
    if n == 0: return (0, 0)
    p = k / n; d = 1 + z * z / n; ce = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d; return max(0, ce - h), min(1, ce + h)
for tag, f in (("MAIN2", "main2.json"), ("HOLDOUT2", "holdout2.json")):
    D = json.load(open(os.path.join(RS, f))); B = [c for c in D["cells"] if c.get("measured") and c["loader"] != "stub_empty"]
    print("=" * 10, tag, "bare runs", len(B))
    G = collections.defaultdict(list)
    for c in B:
        if c["silent_core"]: G[grp(c["loader"], c["fixture"])].append(c)
    for c in B:
        if c["silent_unread"]: G["C modality gap (no text layer / script-rendered)"].append(c)
    # a run can be in both A/B and C only if it has both; keep as-is but report
    both = sum(1 for c in B if c["silent_core"] and c["silent_unread"]); print("runs with both core and unread silent loss:", both)
    for g in sorted(G):
        cs = G[g]; pairs = collections.Counter((c["loader"], c["fixture"].split("_")[0]) for c in cs)
        print("\n[%s] runs %d (%.1f%% of %d) Wilson [%.1f,%.1f]; loader-class pairs %d; loaders %d; families %d" % (g, len(cs), 100 * len(cs) / len(B), len(B), 100 * wil(len(cs), len(B))[0], 100 * wil(len(cs), len(B))[1], len(pairs), len({c["loader"] for c in cs}), len({c["family"] for c in cs})))
        print("  by class:", dict(collections.Counter(c["fixture"].split("_")[0] for c in cs)))
        print("  by loader:", dict(sorted(collections.Counter(c["loader"] for c in cs).items())))
        print("  families:", sorted({c["family"] for c in cs}))
    core = G["A caller-idiom footgun"] + G["B library/engine behaviour"]
    # split group B into sub-mechanisms
    sub = collections.Counter()
    for c in G["B library/engine behaviour"]:
        fx = c["fixture"].split("_")[0]; l = c["loader"]
        sub[("P04 rotation" if fx == "P04" else "P11 truncation" if fx == "P11" else "mammoth headers/footers" if l == "mammoth" else "charset misguess" if l == "txt_charset_normalizer" else "html2text accent stripping" if l == "html2text" else "other:%s/%s" % (l, fx))] += 1
    print("\nGroup B sub-mechanisms (runs):", dict(sub))
    print("silent core loss total", len(core), " minus caller group =", len(G["B library/engine behaviour"]), "; families remaining in B:", sorted({c["family"] for c in G["B library/engine behaviour"]}), len({c["family"] for c in G["B library/engine behaviour"]}))
    # silent-core families by group (Wilson LB>0 rule is implied: >=1/20 any)
    print("\nRECALL WHEN THE LOADER RETURNED SILENTLY (core kinds; loud = raised or novel stderr) vs LOUD RATE, per loader (cluster bootstrap over replicate seeds, 95%)")
    rng = random.Random(1); seeds = sorted({c["seed"] for c in B})
    print("%-6s %-24s %7s %22s %9s %9s" % ("fmt", "loader", "runs", "recall-when-silent", "loud%", "raise%"))
    for fmt in ("pdf", "docx", "pptx", "html", "txt"):
        for l in sorted({c["loader"] for c in B if c["fmt"] == fmt}):
            cs = [c for c in B if c["loader"] == l]
            by = collections.defaultdict(lambda: [0.0, 0])
            for c in cs:
                if c["loud"]: continue
                for k, v in c["by_kind"].items():
                    if k in CORE: by[c["seed"]][0] += v["found"]; by[c["seed"]][1] += v["total"]
            ss = list(by); tot = sum(by[s][1] for s in ss)
            if not tot: print("%-6s %-24s no silent runs with core content" % (fmt, l)); continue
            pt = sum(by[s][0] for s in ss) / tot; bs = []
            for _ in range(1000):
                pk = [rng.choice(ss) for _ in ss]; d = sum(by[s][1] for s in pk); bs.append(sum(by[s][0] for s in pk) / d if d else 1)
            bs.sort()
            print("%-6s %-24s %7d  %.3f [%.3f,%.3f] %8.1f%% %8.1f%%" % (fmt, l, len(cs), pt, bs[25], bs[974], 100 * sum(c["loud"] for c in cs) / len(cs), 100 * sum(c["raised"] for c in cs) / len(cs)))
    # headline substitute: pooled
    for lab, sel in (("all loaders", B),):
        sil = [c for c in sel if not c["loud"]]; f_ = sum(v["found"] for c in sil for k, v in c["by_kind"].items() if k in CORE); t_ = sum(v["total"] for c in sil for k, v in c["by_kind"].items() if k in CORE)
        print("\npooled recall when silent, %s: %.3f over %d silent runs; loud runs %d (%.1f%%)" % (lab, f_ / t_, len(sil), len(sel) - len(sil), 100 * (len(sel) - len(sil)) / len(sel)))
