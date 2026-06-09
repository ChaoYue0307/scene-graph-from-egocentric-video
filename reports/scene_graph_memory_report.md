# Scene Graph Memory Report

## Motivation

Egocentric video becomes more useful when observations are represented as
objects, relations, timestamps, and provenance. A temporal scene graph gives a
simple way to ask what was visible, what the hand interacted with, and what task
state was active.

## Method

The graph builder reads caption annotations, extracts timestamped objects and
interaction text, merges canonical object aliases, attaches SLAM pose previews,
and writes a JSON graph. Optional detector or tracker JSON can be merged with
caption-derived objects while preserving confidence, track ids, and provenance.

## Artifacts

- `scene_graph.json`: objects, frames, relations, segments, metadata.
- `query_results.json`: object memory, interaction, and state query examples.
- `schema.json`: graph contract.
- `top_objects.svg`: object-frequency visual.

## Interpretation

The current graph is transparent and inspectable. It is useful for learning
world-memory structure and query design, but it is not a substitute for a
validated detector, tracker, segmenter, or relation classifier.

## Failure Modes

- Caption object lists can miss visual objects.
- Alias merging can collapse distinct instances.
- Interaction rules can overstate contact or intent.
- Detector and caption sources may disagree.

## Next Work

- Add instance-aware object tracking.
- Add relation confidence calibration.
- Add graph validation against human-labeled queries.
