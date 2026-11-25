"""AMENDMENT 5 follow-up: why do pdfminer-based loaders miss text on /Rotate 90 pages of the corrected P04? Run with .venv_frameworks2 (pdfminer.six) on /tmp-style corrected fixtures.
usage: <venv2>/bin/python -I stage3/p4fix_pdfminer_check.py FIXDIR > results/p4fix_pdfminer_check.txt  (page 2 of seed 20261401 has /Rotate 90)"""
import sys, json, re, os
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
p = os.path.join(sys.argv[1], "20261401", "P04_rotated.pdf"); man = json.load(open(p + ".json")); w = man["units"][1]["words"]
for dv in (False, True):
    got = set(re.findall(r"[a-z0-9]+", extract_text(p, page_numbers=[1], laparams=LAParams(detect_vertical=dv)).lower()))
    print("pdfminer LAParams(detect_vertical=%s), page 2 of seed 20261401 (/Rotate 90): word recall %.2f" % (dv, sum(x in got for x in w) / len(w)))
