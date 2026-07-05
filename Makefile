# C2RB pipeline targets. Run from the repo root; uses the project venv directly.
VENV    := .venv/bin
COUNTRY ?= afghanistan
CONFIG   = countries/$(COUNTRY).yaml
AS_OF   ?= 2026-06-01
WINDOW  ?= 90
EVENT   ?= Armed clash
GEO     ?= 1
FAT     ?= 3

.PHONY: help train score predict notebook pdf test app all

help:            ## list targets
	@grep -E '^[a-z]+:.*##' $(MAKEFILE_LIST) | awk -F ':.*## ' '{printf "  make %-10s %s\n", $$1, $$2}'

test:            ## run the pytest smoke suite
	$(VENV)/python -m pytest tests/ -q

train:           ## calibrate P0 + validate + save model.joblib (COUNTRY=...)
	$(VENV)/python train.py --config $(CONFIG)

score:           ## rank roads for a window (AS_OF=... WINDOW=...)
	$(VENV)/python score.py --config $(CONFIG) --as-of $(AS_OF) --window-days $(WINDOW)

predict:         ## event-level P(blocked) (EVENT=... GEO=... FAT=...)
	$(VENV)/python predict.py --config $(CONFIG) --sub-event-type "$(EVENT)" \
		--geo-precision $(GEO) --fatalities $(FAT)

notebook:        ## regenerate the notebook from build_notebook.py and execute it
	$(VENV)/python build_notebook.py
	$(VENV)/jupyter nbconvert --to notebook --execute --inplace \
		--ExecutePreprocessor.timeout=900 conflict_road_blockage.ipynb

pdf:             ## recompile docs/methodology.pdf with tectonic
	cd docs && PATH="/opt/homebrew/bin:$$PATH" tectonic methodology.tex

app:             ## launch the Streamlit app
	$(VENV)/python -m streamlit run app.py

all: test notebook pdf   ## everything that verifies the repo end-to-end
