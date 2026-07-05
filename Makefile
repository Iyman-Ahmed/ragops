.PHONY: install test lint eval gate calibrate answer-gate run ingest demo-regression clean

VENV ?= .venv
PY   := $(VENV)/bin/python
PIP  := $(VENV)/bin/pip

install:                      ## create venv + install pinned deps
	python3 -m venv $(VENV)
	$(PIP) install -q --upgrade pip
	$(PIP) install -q -r requirements.txt

lint:
	$(VENV)/bin/ruff check .

test:
	$(PY) -m pytest

eval:                         ## full report (retrieval always; generation if an endpoint is up)
	$(PY) -m eval.evaluate

gate:                         ## L1 deterministic retrieval gate (the CI centerpiece)
	$(PY) -m eval.retrieval_gate

answer-gate:                  ## L3 generation gate (loud-disarm without an endpoint)
	$(PY) -m eval.answer_gate

calibrate:                    ## evaluate the eval — TPR/FPR of the gate on seeded regressions
	$(PY) -m eval.calibrate

run:                          ## serve the API on :8000
	$(VENV)/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

demo-regression:              ## reproduce the money shot: gate goes RED on an embedding swap
	@echo ">>> Clean pipeline (gate should PASS):"
	@$(PY) -m eval.retrieval_gate; echo "exit=$$?"
	@echo ""
	@echo ">>> Injected regression EMBED_MODEL=hash-64 (gate should FAIL, exit 1):"
	@EMBED_MODEL=hash-64 $(PY) -m eval.retrieval_gate; echo "exit=$$?"

clean:
	rm -rf chroma_db mlruns .pytest_cache .ruff_cache
