#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def bbox_for(frame_idx: int, object_idx: int) -> list[int]:
    x1 = 48 + (object_idx * 61 + frame_idx * 17) % 420
    y1 = 36 + (object_idx * 43 + frame_idx * 11) % 250
    width = 72 + (object_idx * 7) % 46
    height = 68 + (frame_idx * 5) % 44
    return [x1, y1, x1 + width, y1 + height]


def generate(graph: dict, max_frames: int) -> dict:
    detections = []
    for frame_idx, frame in enumerate(graph.get("frames", [])[:max_frames]):
        objects = []
        for object_idx, name in enumerate(frame.get("objects", [])):
            objects.append({
                "label": name,
                "track_id": f"{name.lower().replace(' ', '_')}-{object_idx}",
                "confidence": round(0.78 + 0.03 * ((frame_idx + object_idx) % 5), 2),
                "bbox_xyxy": bbox_for(frame_idx, object_idx),
            })
        detections.append({"timestamp": frame["timestamp"], "frame_index": frame_idx, "objects": objects})
    return {
        "source": "annotation-grounded detector/tracker fixture for exercising the graph merge path",
        "detections": detections,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a small detector/tracker JSON fixture from an existing scene graph.")
    parser.add_argument("--graph-json", type=Path, default=Path("outputs/sample_graph/scene_graph.json"))
    parser.add_argument("--output-json", type=Path, default=Path("docs/data/sample_detections.json"))
    parser.add_argument("--max-frames", type=int, default=24)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    graph = json.loads(args.graph_json.read_text(encoding="utf-8"))
    payload = generate(graph, args.max_frames)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"detections={len(payload['detections'])} output={args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
