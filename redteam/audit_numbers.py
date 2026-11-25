"""Recount Table 3, P09, stub, 3080 vs 3060 from results/main2.json + holdout2.json. usage: .venv/bin/python -I redteam/audit_numbers.py"""
import json, collections, os
RS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")
for tag, f in (("MAIN2", "main2.json"), ("HOLDOUT2", "holdout2.json")):
    D = json.load(open(os.path.join(RS, f))); C = D["cells"]
    print("==", tag, "all cells", len(C), "stub", sum(c["loader"] == "stub_empty" for c in C), "unmeasured", sum(not c.get("measured") for c in C))
    B = [c for c in C if c.get("measured") and c["loader"] != "stub_empty"]; print("bare", len(B))
    def loud_wrap(c, k="R"): return c["wrap"][k]["loud"] is not None
    # P09: loaders with silent_unread
    for fx in ("P07_image_only", "P09_form_only", "H04_js_rendered"):
        g = collections.defaultdict(int)
        for c in B:
            if c["fixture"] == fx and c["silent_unread"]: g[c["loader"]] += 1
        print(fx, len(g), "loaders:", dict(g))
    # Table 3 decomposition
    loud = [c for c in B if c["raised"] or c.get("stderr_novel")]; print("A1 loud (raised or novel stderr)", len(loud), "raised", sum(c["raised"] for c in B))
    ref = [c for c in B if loud_wrap(c)]; print("R refused (loud incl loader raised)", len(ref))
    ref_loaderraised = [c for c in ref if c["raised"]]; ref_cons = [c for c in ref if not c["raised"]]
    print("  of which loader raised", len(ref_loaderraised), "ConservationError", len(ref_cons))
    accepted = [c for c in B if not loud_wrap(c)]; print("R returned (not refused)", len(accepted))
    print("  accepted & loss_any False (clean accepted)", sum(not c["loss_any"] for c in accepted))
    ua = [c for c in accepted if c["loss_any"]]; print("  accepted & loss_any True (declared-unreadable etc)", len(ua))
    print("   by fixture/loader class:", dict(collections.Counter((c["fixture"].split('_')[0]) for c in ua)))
    print("   by fixture:", dict(collections.Counter(c["fixture"] for c in ua)))
    st = collections.Counter(s for c in ua for s in c["wrap"]["R"]["statuses"].elements() ) if False else None
    print("   with declared_unreadable unit:", sum("declared_unreadable" in c["wrap"]["R"]["statuses"] for c in ua), " silent drops among them:", sum(c["wrap"]["R"]["silent_drops"] for c in ua))
    print("   accepted lossy w/o declared_unreadable:", [(c["fixture"], c["loader"], c["wrap"]["R"]["statuses"], c["by_kind"]) for c in ua if "declared_unreadable" not in c["wrap"]["R"]["statuses"]][:5])
    # selective-removal runs (trafilatura/html2text/bs4_sep etc): what did check do?
    sel = [c for c in B if c["fmt"] == "html" and c["silent_sel"]]
    print("HTML silent_sel runs (boilerplate/csshidden removed by design)", len(sel), dict(collections.Counter((c["loader"], c["fixture"].split("_")[0]) for c in sel)))
    print("  check refused them:", sum(loud_wrap(c) for c in sel), " accepted:", sum(not loud_wrap(c) for c in sel), "; refusal msgs", collections.Counter(c["wrap"]["R"]["loud"] for c in sel if loud_wrap(c)))
    print("  loss_any among them:", sum(c["loss_any"] for c in sel))
    # all html runs by loader x fixture: check refused vs loader loss
    t = collections.Counter()
    for c in B:
        if c["fmt"] == "html" and c["loader"] in ("trafilatura", "html2text", "bs4_sep"):
            t[(c["loader"], c["fixture"].split("_")[0], "refused" if loud_wrap(c) else "accepted", "loss" if c["loss_any"] else "noloss")] += 1
    for k, v in sorted(t.items()): print("   ", k, v)
    # false alarms: refused & no loss_any
    fa = [c for c in B if loud_wrap(c) and not c["loss_any"]]; print("false alarms (refused, loss_any False)", len(fa), dict(collections.Counter(c["fmt"] for c in fa)))
    fa_sel = [c for c in B if loud_wrap(c) and c["silent_sel"] and not (c["silent_core"] or c["silent_unread"])]
    print("refused where only selective removal happened (loader did what it was designed):", len(fa_sel))
    print("refused & loss_any False & fmt html:", sum(1 for c in fa if c["fmt"] == "html"))
