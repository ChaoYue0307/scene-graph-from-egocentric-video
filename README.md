# Scene Graph From Egocentric Video

Structured world-memory demo for one Xperience-10M egocentric sample.

The repo turns caption object annotations, interaction text, task segments, and
SLAM camera poses into a temporal scene graph. It is intentionally lightweight
and rule-based so the data contract is clear before adding detector/segmenter
models.

This maps to:

- scene graphs from first-person video,
- object-centric and space-centric representations,
- hand-object interaction memory,
- spatial reasoning over camera-pose-tagged frames,
- agent world models that can answer timeline and state queries.

Raw videos, `annotation.hdf5`, and `.rrd` files stay outside git.

## Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/scene_graph_demo.py \
  --data-root /Users/chaoyue/Library/CloudStorage/Dropbox/Ropedia/data/sample/xperience-10m-sample \
  --output-dir outputs/sample_graph \
  --max-frames 80 \
  --query object:kettle \
  --query interactions \
  --query state:last
```

## Outputs

- `scene_graph.json`: temporal scene graph with frames, objects, relations,
  segments, provenance, confidence scores, and camera-pose previews.
- `schema.json`: compact JSON schema for the graph contract.
- `query_results.json`: example query outputs for object timelines,
  hand-object interactions, and current/previous state.

## Relation Sources

The current demo uses caption-derived signals first:

- `visible_in`: object appears in caption object list for a timestamp.
- `hand_grasps`, `hand_contacts`, `hand_pours_with`, `hand_moves_toward`:
  rule-based relation from interaction text and object-name matching.
- `action_active`: active caption action at a sampled timestamp.

The future detector hook is explicit in the graph provenance: replace or merge
`caption.objects` with YOLO/SAM-style detections and masks, then keep the same
JSON schema for downstream query and memory tasks.

## Example Queries

```bash
python scripts/scene_graph_demo.py --query object:kettle
python scripts/scene_graph_demo.py --query interactions
python scripts/scene_graph_demo.py --query state:last
```

These queries are simple by design. The goal is to make the memory structure
auditable before connecting it to a language model or embodied-agent planner.
