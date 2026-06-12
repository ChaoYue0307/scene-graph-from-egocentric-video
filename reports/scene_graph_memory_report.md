# Scene Graph Memory Report

## Motivation

Egocentric video becomes more useful when observations are represented as
objects, relations, timestamps, and provenance. A temporal scene graph gives a
simple way to ask what was visible, what the hand interacted with, what task
state was active — and now, where the wearer was when an object was last seen.

## Method

The graph builder reads caption annotations, extracts timestamped objects and
interaction text, merges canonical object aliases, attaches SLAM pose previews,
and writes a JSON graph. Each object observation with a SLAM pose appends the
wearer's camera position to that object's `camera_trail`, turning the graph
into a queryable spatial memory (`where:<object>`). Optional detector or
tracker JSON can be merged with caption-derived objects while preserving
confidence, track ids, and provenance.

Graph quality is scored against 33 human-labeled QA pairs
(`eval/qa_pairs.json`) covering object memory, alias resolution, visibility,
interactions, task state, temporal order, and the spatial proxy. The current
caption-grounded graph scores 33/33; the value of the benchmark is regression
protection and honest failure surfacing once noisier sources (detectors,
trackers) feed the graph.

## Artifacts

- `scene_graph.json`: objects, frames, relations, segments, metadata, camera trails.
- `query_results.json`: object memory, interaction, state, and where query examples.
- `qa_results.json`: QA accuracy with per-question-type breakdown.
- `schema.json`: graph contract.
- `top_objects.svg`: object-frequency visual.
- `visual_detections.json`: OpenCV contour proposals from real video frames.
- `graph_comparison.json`: caption-only versus detector-merged graph comparison.

## Interpretation

The current graph is transparent and inspectable. It is useful for learning
world-memory structure and query design, but it is not a substitute for a
validated detector, tracker, segmenter, or relation classifier.

The spatial memory stores the wearer's camera position at sighting time — an
egocentric proxy for object location, explicitly labeled as such in
provenance. For tabletop manipulation the proxy is tight (objects are within
arm's reach), but it does not survive far-field observations; triangulating
object positions from bounding boxes plus poses is the natural upgrade.

The detector path includes a visual-proposal option that reads real video
frames, extracts contour-based bounding boxes, and stores detector-style
confidence, track id, and `bbox_xyxy` fields. Object labels are still
associated with graph-visible names, so this is a stronger integration test
rather than a trained recognition result.

## Failure Modes

- Caption object lists can miss visual objects.
- Alias merging can collapse distinct instances.
- Interaction rules can overstate contact or intent.
- Detector and caption sources may disagree.
- The camera-position proxy misplaces objects seen from afar.

## Next Work

- Add instance-aware object tracking (track ids are already preserved).
- Add relation confidence calibration.
- Triangulate object positions from detector boxes and SLAM poses.
- Re-score the QA set with detector-sourced graphs to measure real perception
  accuracy against the same gold answers.
