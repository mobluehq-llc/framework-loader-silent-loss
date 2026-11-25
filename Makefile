PY ?= python3
.PHONY: verify
verify:
	$(PY) -I verify.py
