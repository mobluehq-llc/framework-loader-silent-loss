"""Post-hoc (not registered). usage: .venv_frameworks/bin/python -I stage3/status_checks.py docling | .venv_frameworks2/bin/python -I stage3/status_checks.py haystack
docling: ConversionResult.status and .errors for the 7 PDF/ DOCX/PPTX classes of seeds 20261401-05 (calls as in fw_run.py).
haystack: length of the returned documents list for skipped inputs (T02-T05, P11) and the presence of PPTXToDocument."""
import sys, os, glob, collections, warnings
warnings.simplefilter("ignore"); H = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = os.path.join(H, "fixtures3_fw")
if sys.argv[1] == "docling":
    from docling.document_converter import DocumentConverter
    dc = DocumentConverter(); C = collections.Counter()
    for sd in sorted(os.listdir(R))[:5]:
        for f in sorted(glob.glob(os.path.join(R, sd, "*"))):
            if f.endswith(".json") or not f.endswith((".pdf", ".docx", ".pptx", ".html")): continue
            try: r = dc.convert(f); C[(os.path.basename(f).split("_")[0], str(r.status), len(r.errors))] += 1
            except BaseException as e: C[(os.path.basename(f).split("_")[0], "RAISED " + type(e).__name__, 0)] += 1
    for k, v in sorted(C.items()): print("class %s status %s errors %d: %d runs" % (*k, v))
else:
    import haystack, haystack.components.converters as cv
    print("haystack-ai", haystack.__version__, "PPTXToDocument present:", hasattr(cv, "PPTXToDocument"))
    sd = sorted(os.listdir(R))[0]; U = cv.PyPDFToDocument(); T = cv.TextFileToDocument()
    for cls, conv in (("T02_utf16_bom.txt", T), ("T03_latin1.txt", T), ("T04_cp1252.txt", T), ("T05_mixed_encoding.txt", T), ("P11_truncated.pdf", U), ("T01_utf8.txt", T)):
        o = conv.run(sources=[os.path.join(R, sd, cls)]); print(cls, "keys", sorted(o), "documents:", len(o["documents"]))
    d = cv.DOCXToDocument().run(sources=[os.path.join(R, sd, "D04_nested_table.docx")])["documents"]; print("D04 documents", len(d))
