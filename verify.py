#!/usr/bin/env python3
"""Regenerate every number and table of the note from the stored results and require identity with the
paper source in paper_source/; also recompute two Table I counts directly from the raw JSON.
Works in a temporary copy (gunzips the stored results there). Exit 1 on any mismatch. Usage: python3 -I verify.py"""
import sys, os, json, gzip, shutil, subprocess, tempfile, filecmp
H = os.path.dirname(os.path.abspath(__file__)); bad = []
def check(name, ok, detail=""):
    print(("PASS " if ok else "FAIL ") + name + (" " + detail if detail else "")); 
    if not ok: bad.append(name)
tmp = tempfile.mkdtemp()
try:
    shutil.copytree(os.path.join(H, "paper_note"), os.path.join(tmp, "paper_note")); shutil.copytree(os.path.join(H, "results"), os.path.join(tmp, "results"))
    for f in os.listdir(os.path.join(tmp, "results")):
        if f.endswith(".json.gz"):
            with gzip.open(os.path.join(tmp, "results", f)) as a, open(os.path.join(tmp, "results", f[:-3]), "wb") as b: shutil.copyfileobj(a, b)
    r = subprocess.run([sys.executable, "-I", os.path.join(tmp, "paper_note", "make_numbers.py")], capture_output=True, text=True)
    check("make_numbers.py runs (its literal-string assertions hold)", r.returncode == 0, r.stderr[-300:])
    for f in ["numbers", "table_fw", "table_fw_clean", "table_fw_p4", "table_fw_p11", "table_lib", "table_prereg"]:
        a, b = os.path.join(tmp, "paper_note", f + ".tex"), os.path.join(H, "paper_source", f + ".tex")
        check("regenerated %s.tex identical to paper_source" % f, os.path.exists(a) and os.path.exists(b) and filecmp.cmp(a, b, shallow=False))
    # Table I, first row, straight from the raw results: LangChain BSHTMLLoader, 120 HTML runs, all silent, none raised
    cells = json.load(open(os.path.join(tmp, "results", "redteam_fw_s2_all.json")))
    lc = [c for c in cells if c["loader"] == "lc_html"]
    n = len(lc); sil = sum(bool(c.get("silent_core", c.get("loss_core"))) for c in lc if not c["raised"]); rai = sum(bool(c["raised"]) for c in lc)
    check("LangChain BSHTMLLoader HTML: 120 runs, 120 with missing tokens, 0 exceptions", (n, sil, rai) == (120, 120, 0), "got n=%d silent=%d raised=%d" % (n, sil, rai))
    first = open(os.path.join(H, "paper_source", "table_fw.tex")).read().splitlines()[0]
    check("Table I first row reads 120/120 and 0 exceptions", "120/120 & 0" in first, first[:100])
finally:
    shutil.rmtree(tmp, ignore_errors=True)
print("verify: %s" % ("ALL PASS" if not bad else "FAILED: " + ", ".join(bad))); sys.exit(1 if bad else 0)
