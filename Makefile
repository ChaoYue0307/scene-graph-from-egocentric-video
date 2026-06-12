PYTHON ?= python3

.PHONY: test help visuals detector-fixture visual-detections qa-eval pages

test:
	$(PYTHON) -m pytest -q

help:
	$(PYTHON) scripts/scene_graph_demo.py --help

visuals:
	$(PYTHON) scripts/render_graph_visuals.py

detector-fixture:
	$(PYTHON) scripts/generate_detector_fixture.py

visual-detections:
	$(PYTHON) scripts/generate_visual_detections.py

qa-eval:
	$(PYTHON) scripts/evaluate_graph_qa.py

pages:
	@echo "https://chaoyue0307.github.io/scene-graph-from-egocentric-video/"
