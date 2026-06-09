# Concepts: Scene Graphs From Egocentric Video

## Scene Graph

A scene graph represents the world as objects and relations. Instead of storing
only pixels, it stores structured facts:

```text
object: kettle
relation: hand_grasps(kettle)
time: 72863804786785
```

This structure is useful because it can be queried, inspected, and passed to an
agent or planner.

## Object-Centric Memory

Object-centric memory keeps a record for each object: when it was first seen,
when it was last seen, how many times it appeared, and which aliases refer to
it.

In egocentric video, objects may disappear behind hands or leave the field of
view. Tracking object memory across time helps preserve task context.

## Temporal Relation

A temporal relation is a fact with a timestamp. For example:

```text
visible_in(kettle, frame_12)
hand_grasps(kettle) at timestamp T
action_active(person, "Move kettle") at timestamp T
```

Temporal relations turn a static graph into a timeline.

## Hand-Object Interaction

Hand-object interaction describes how the actor's hands relate to objects:
moving toward, grasping, placing, pouring, or touching. These relations are
important for understanding intention, not just appearance.

## Spatial Reasoning

Spatial reasoning asks where things are and how they relate in space. This repo
stores SLAM camera poses with frames, which is a first step toward space-aware
queries.

Examples:

- What object was visible when the camera was near the dripper?
- Which object did the hand interact with before the kettle moved?
- What was the current task state at the last observed timestamp?

## Provenance

Provenance records where each fact came from. A relation may come from caption
text, object annotations, or future detector outputs. Provenance makes the graph
auditable and easier to improve.

## Detector Hook

The current graph uses caption annotations. A future detector or segmenter can
replace or merge those object sources while keeping the same graph schema:

```text
video frame -> detector/segmenter -> objects/masks -> scene graph -> queries
```
