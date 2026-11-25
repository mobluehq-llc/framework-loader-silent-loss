# Default document loaders: code and fixtures bundle

Accompanies the preprint "Default document loaders in AI frameworks can lose content without an error: a short measurement note"
(Adam Faust, MOBLUEHQ, Inc.). Version 1.0 (note v9). Verify: `make verify` (or `python3 -I verify.py`) regenerates every number and table from the stored results and checks them against `paper_source/`.

## Layout
- `paper_source/` LaTeX source of the note (v9) with the generated tables; `verify.py` compares the regenerated tables to these.
- `stage2/gen2.py` fixture generator: `python stage2/gen2.py --seed N --out DIR` (one file per class, ground truth in `<file>.json`). Seeds 20261401-20261420 were used for the framework rows; the same seed reproduces the same words (checked for P04, D04, T03, H04 of seed 20261401, and T03 byte for byte). `gen_fixtures.py` is an earlier generator (different class file names).
- `fixtures_sample_seed_20261401/` one complete seed of constructed files with manifests (its P04 file is the withdrawn defective one); `fixtures_p4fix_sample/` the corrected P04 file for the same seed.
- `stage3/` the harness: `loaders3.py`, `run3.py` (metric: token multiset recall per kind), `conserve2.py`, `fw_run.py` (LangChain, LlamaIndex, Docling defaults), `fw2_run.py` (Haystack, Unstructured, MarkItDown defaults), `fw_real.py` (real files), and the post-hoc checks `p4_clip_check.py`, `docling_md_check.py`, `status_checks.py`. `stage2/run2.py` runs the library calls.
- `results/` stored outputs. The JSON files are what every number in the note is computed from; `main2.json.gz` and `holdout2.json.gz` must be gunzipped before `paper_note/make_numbers.py` runs. Text summaries are included, among them `p4_clip_check.txt`, `docling_markdown_check.txt`, `status_checks_*.txt`.
- `paper_note/make_numbers.py` writes every number and table in the note from the stored results and asserts literal strings in the summaries.
- `requirements/` pinned environments: library calls (`requirements.lock.txt`, `requirements2.lock.txt`), LangChain/LlamaIndex/Docling (`requirements_frameworks_langchain_llamaindex_docling.lock.txt`), Haystack/Unstructured/MarkItDown (`requirements_fw2.lock.txt`). Python 3.12, CPU only.
- `realworld/` manifests (URL, date, sha256) and scripts for the public real files. The files themselves are NOT redistributed; fetch them with `fetch_public.py`.

## Reproduce one framework row
    python -m venv v && v/bin/pip install -r requirements/requirements_frameworks_langchain_llamaindex_docling.lock.txt
    mkdir seeds && python stage2/gen2.py --seed 20261401 --out seeds/20261401
    v/bin/python -I stage3/fw_run.py seeds OUT.json

`fw_run.py` takes a directory holding one folder per seed. Paths inside some scripts assume the layout of the original repository (`fixtures3_fw`); adjust them if you move files.

## Scope and caveats
Constructed files, pinned versions, default arguments only. The first P4 (rotated pages) test file was defective (text outside the page box on pages rotated 90 or 270 degrees; `results/p4_clip_check.txt`) and every number from it is withdrawn. `stage2/gen2_p4fix.py` writes the corrected file (one changed constant); the registered rerun is `stage3/p4fix_run.py`, results `results/p4fix*.txt|json`: no loss for LangChain, LlamaIndex, Haystack, Docling, PyMuPDF; Unstructured 0.39 and MarkItDown 0.61 (pdfminer default layout analysis skips vertical text). Untested: Haystack `PPTXToDocument` and `MarkdownToDocument`, text files in LangChain and Docling, PPTX in LangChain, Unstructured OCR and hi_res strategies.
