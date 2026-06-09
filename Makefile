PYTHON ?= python3

.PHONY: test help visuals pages

test:
	$(PYTHON) -m pytest -q

help:
	$(PYTHON) scripts/scene_graph_demo.py --help

visuals:
	$(PYTHON) scripts/render_graph_visuals.py

pages:
	@echo "https://chaoyue0307.github.io/scene-graph-from-egocentric-video/"
