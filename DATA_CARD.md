# Data Card

## Source

This project uses one local Xperience-10M sample episode of a pour-over coffee
task. Raw videos and `annotation.hdf5` stay outside the repository.

## Inputs Used

- Frame-level caption records from `annotation.hdf5`.
- Object mentions and hand-object interaction text from the sample annotations.

## Scope

The data is used to demonstrate how egocentric video annotations can become a
temporal scene graph with objects, relations, provenance, and simple queries.

## Limitations

- Single episode.
- Object extraction is annotation-driven, not a trained detector.
- Relations are heuristic and should be checked before use in downstream systems.
- Canonical object aliases are intentionally small and task-specific.
