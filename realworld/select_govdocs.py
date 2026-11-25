"""GovDocs1 subset 864 (PREREG S3b): first 50 pdf, 20 html, 20 txt by sorted name, <=20 MB. Copies to realworld/raw/gov/<ext>/ and writes MANIFEST_gov.tsv. usage: python3 -I realworld/select_govdocs.py"""
import os, glob, shutil, hashlib
H = os.path.dirname(os.path.abspath(__file__)); src = os.path.join(H, "raw", "govdocs", "x"); rows = []
for ext, n in (("pdf", 50), ("html", 20), ("txt", 20)):
    fs = sorted(glob.glob(os.path.join(src, "**", "*." + ext), recursive=True), key=os.path.basename); fs = [f for f in fs if os.path.getsize(f) <= 20 * 2**20][:n]
    os.makedirs(os.path.join(H, "raw", "gov", ext), exist_ok=True)
    for f in fs:
        d = os.path.join(H, "raw", "gov", ext, os.path.basename(f)); shutil.copy(f, d); b = open(d, "rb").read()
        rows.append((ext, os.path.basename(f), "digitalcorpora govdocs1 zipfiles/864.zip", hashlib.sha256(b).hexdigest(), len(b)))
open(os.path.join(H, "MANIFEST_gov.tsv"), "w").write("kind\tfile\tsource\tsha256\tbytes\n" + "\n".join("\t".join(map(str, r)) for r in rows) + "\n"); print(len(rows))
