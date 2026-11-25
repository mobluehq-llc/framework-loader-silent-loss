"""usage: run2.py --fixtures DIR --out results.json [--workers 4] | run2.py --cell LOADER PATH OUT (child). DIR holds one subdir per seed."""
import argparse, glob, json, os, re, subprocess, sys, time, collections
from concurrent.futures import ThreadPoolExecutor
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import loaders3 as L
from conserve2 import account, ConservationError, toks, recall, reference
CORE = {"text", "hidden", "body", "table", "header", "footer", "group", "notes", "entity"}
UNREAD = {"image", "form", "dynamic"}
CTRL = {"pdf": "P01_text", "docx": "D01_body", "pptx": "S01_textboxes", "html": "H01_body", "txt": "T01_utf8"}

# S2 run: competent pipelines (stage3/loaders3.py); wrapper conserve2 unchanged
def child(lid, path, out):
    import warnings, logging
    warnings.simplefilter("always"); warnings.simplefilter("ignore", ResourceWarning); logging.basicConfig(level=logging.WARNING)
    res = dict(raised=False, exc=None, pages=None)
    try: res["pages"] = L.load(lid, path)
    except BaseException as e: res.update(raised=True, exc=type(e).__name__ + ": " + str(e)[:200])
    with open(out, "w") as fh: json.dump(res, fh)

def cell(lid, path, tmp):
    out = tmp + ".cell.json"
    if os.path.exists(out): os.remove(out)
    try:
        p = subprocess.run([sys.executable, "-I", os.path.abspath(__file__), "--cell", lid, path, out], capture_output=True, timeout=120)
        err = p.stderr.decode("utf8", "replace"); rc = p.returncode
    except subprocess.TimeoutExpired: return dict(measured=False, why="timeout")
    if not os.path.exists(out): return dict(measured=False, why="crash rc=%s" % rc, stderr=err[-300:])
    r = json.load(open(out)); r.update(measured=True, stderr=err[-400:], stderr_bytes=len(err.strip()), rc=rc); return r

def metrics(man, lid, c):
    pages = c["pages"] or []; fmt = man["format"]; units = man["units"]; whole = toks("\n".join(pages)); bykind = {}
    pagegrain = fmt == "pdf" and lid not in L.DOCGRAIN
    for i, u in enumerate(units):
        if not u["words"]: continue
        R = collections.Counter(); [R.update(toks(w)) for w in u["words"]]
        O = toks(pages[i]) if (pagegrain and i < len(pages)) else (whole if not pagegrain else collections.Counter())
        k = bykind.setdefault(u["kind"], [0.0, 0, 0]); k[0] += sum(min(v, O[t]) for t, v in R.items()); k[1] += sum(R.values()); k[2] += 1
    pce = (len(pages) - man["page_count"]) if pagegrain else 0
    mis = 0
    if pagegrain:
        for i, u in enumerate(units):
            if not u["words"]: continue
            R = set(t for w in u["words"] for t in toks(w)); here = toks(pages[i]) if i < len(pages) else {}
            if not any(t in here for t in R) and any(t in toks(pages[j]) for j in range(len(pages)) if j != i for t in R): mis += 1
    return dict(by_kind={k: dict(found=v[0], total=v[1], units=v[2]) for k, v in bykind.items()}, page_count_error=pce, misnumbered=mis)

def evaluate(man, lid, c, mu, path):
    fmt = man["format"]
    try: a = account(path, fmt, lid, c, mu, L.DOCGRAIN); st, err = a["units"], a["loud"]
    except ConservationError as e: return dict(loud="ConservationError: %s" % e, statuses={}, silent_drops=0, uncovered_partial=0, st=[])
    except Exception as e: return dict(loud="AccountantFault: %s: %s" % (type(e).__name__, e), statuses={}, silent_drops=0, uncovered_partial=0, st=[])
    w = dict(loud=err, statuses=dict(collections.Counter(st)), st=st, silent_drops=0, uncovered_partial=0)
    if err is None:
        pages = c["pages"]; pagegrain = fmt == "pdf" and lid not in L.DOCGRAIN
        if pagegrain:
            for i, u in enumerate(man["units"]):
                if not u["words"]: continue
                R = collections.Counter(); [R.update(toks(x)) for x in u["words"]]; s = st[i] if i < len(st) else "read"
                if s in ("read", "declared_empty") and recall(R, toks(pages[i]) if i < len(pages) else collections.Counter()) < 1: w["silent_drops"] += 1
        else:
            whole = toks("\n".join(pages))
            if st[0] in ("read", "declared_empty"):
                for u in man["units"]:
                    R = collections.Counter(); [R.update(toks(x)) for x in u["words"]]
                    if R and recall(R, whole) < 1: w["silent_drops"] += 1
    return w

def work(job):
    seed, mp, lid, tmpd = job; man = json.load(open(mp)); path = mp[:-5]; fmt = man["format"]
    c = cell(lid, path, os.path.join(tmpd, "%s_%s__%s" % (seed, man["id"], lid)))
    rec = dict(seed=seed, fixture=man["id"], fmt=fmt, loader=lid, family=L.FAMILY[lid], **{k: v for k, v in c.items() if k != "pages"})
    if c.get("measured"):
        rec.update(metrics(man, lid, c), raised=c["raised"], exc=c.get("exc"), n_pages_out=len(c["pages"] or []))
        rec["wrap"] = {mu or "R": evaluate(man, lid, c, mu, path) for mu in (None, "M1", "M2", "M3")}
    return rec

def run(fix, outp, workers):
    tmpd = outp + ".tmp"; os.makedirs(tmpd, exist_ok=True); jobs = []; refcheck = []
    for sd in sorted(glob.glob(os.path.join(fix, "*"))):
        seed = os.path.basename(sd)
        for mp in sorted(glob.glob(os.path.join(sd, "*.json"))):
            man = json.load(open(mp)); fmt = man["format"]
            for lid in L.IDS[fmt] + (["stub_empty"] if man["id"] == CTRL[fmt] and fmt == "pdf" else []): jobs.append((seed, mp, lid, tmpd))
            # instrument check (c): independent reference vs truth on kinds it can see
            vis = {"pdf": {"text", "hidden", "form"}, "docx": None, "pptx": None, "html": {"body", "table", "entity", "boilerplate", "csshidden"}, "txt": None}[fmt]
            try:
                Rr = reference(mp[:-5], fmt); Rt = collections.Counter()
                for u in man["units"]:
                    if vis is None or u["kind"] in vis:
                        for w in u["words"]: Rt.update(toks(w))
                refcheck.append(dict(seed=seed, fixture=man["id"], equal=(Rr == Rt), ref_only=sum((Rr - Rt).values()), truth_only=sum((Rt - Rr).values())))
            except ConservationError as e: refcheck.append(dict(seed=seed, fixture=man["id"], equal=None, why=str(e)))
    with ThreadPoolExecutor(workers) as ex: cells = list(ex.map(work, jobs))
    norm = lambda s: re.sub(r"[0-9]+|/[^ :]*", "#", (s or ""))
    base = {(c["seed"], c["fmt"], c["loader"]): norm(c.get("stderr")) for c in cells if c.get("measured") and c["fixture"] == CTRL[c["fmt"]]}
    for c in cells:
        if not c.get("measured"): continue
        c["stderr_novel"] = c["stderr_bytes"] > 0 and norm(c.get("stderr")) != base.get((c["seed"], c["fmt"], c["loader"]), "")
        c["loud"] = bool(c["raised"] or c["stderr_novel"])
        grp = lambda ks: any(v["found"] < v["total"] for k, v in c["by_kind"].items() if k in ks)
        c["loss_core"] = grp(CORE) or c["page_count_error"] != 0 or c["misnumbered"] > 0
        c["loss_any"] = any(v["found"] < v["total"] for v in c["by_kind"].values()) or c["page_count_error"] != 0 or c["misnumbered"] > 0
        c["silent_core"] = c["loss_core"] and not c["loud"]; c["silent_unread"] = grp(UNREAD) and not c["loud"]
        c["silent_sel"] = grp({"boilerplate", "csshidden"}) and not c["loud"]
    json.dump(dict(fixtures=fix, cells=cells, refcheck=refcheck, time=time.strftime("%F %T")), open(outp, "w"), indent=1, default=str)
    print("cells", len(cells), "refcheck", len(refcheck))

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--fixtures"); ap.add_argument("--out"); ap.add_argument("--workers", type=int, default=4); ap.add_argument("--cell", nargs=3)
    a = ap.parse_args()
    if a.cell: child(*a.cell)
    else: run(a.fixtures, a.out, a.workers)
