# Evaluation Card

## Task

Build a temporal scene graph from egocentric annotations and answer simple
world-memory queries.

## Artifacts To Inspect

- `scene_graph.json`: objects, frames, relations, and metadata.
- `query_results.json`: outputs for object memory, interaction, and state queries.
- `schema.json`: expected graph structure.
- `top_objects.svg`: frequency summary for canonical objects.

## Success Criteria

A useful graph should keep timestamps, preserve provenance, merge obvious object
aliases, and answer queries without needing raw video at query time.

## Known Failure Modes

Caption-derived objects can miss visual entities, merge distinct instances, or
overstate relations. A production system should combine this schema with object
detection, tracking, segmentation, and relation confidence calibration.
