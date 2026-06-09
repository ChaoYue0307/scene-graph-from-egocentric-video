#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


SCHEMA = {
    "type": "object",
    "required": ["metadata", "frames", "objects", "relations", "segments", "provenance"],
    "properties": {
        "metadata": {"type": "object"},
        "frames": {"type": "array", "description": "Timestamped egocentric observations."},
        "objects": {"type": "object", "description": "Object-centric memory keyed by normalized object id."},
        "relations": {"type": "array", "description": "Temporal relations such as visible_in and hand_interacts_with."},
        "segments": {"type": "array", "description": "Task/subtask/action intervals."},
        "provenance": {"type": "object", "description": "How each field was generated."},
    },
}

OBJECT_ALIASES = {
    "gooseneck_kettle": "kettle",
    "glass_kettle": "kettle",
    "coffee_dripper": "dripper",
    "ceramic_dripper": "dripper",
    "digital_scale": "scale",
    "water_bottle": "bottle",
    "glass_carafe": "carafe",
}


def load_caption(annotation: Path) -> dict:
    import h5py

    with h5py.File(annotation, "r") as h5:
        raw = h5["caption"][()]
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    return json.loads(raw)


def load_slam_pose_preview(annotation: Path) -> dict[str, dict]:
    import h5py
    import numpy as np

    with h5py.File(annotation, "r") as h5:
        names = [np.asarray(x).tobytes().decode("utf-8", errors="replace").strip("\x00") for x in h5["slam/frame_names"]]
        trans = np.asarray(h5["slam/trans_xyz"], dtype=float)
        quat = np.asarray(h5["slam/quat_wxyz"], dtype=float)
    poses = {}
    for name, t, q in zip(names, trans, quat, strict=True):
        stem = name.rsplit(".", 1)[0]
        poses[stem] = {
            "position_xyz": [round(float(x), 6) for x in t],
            "quaternion_wxyz": [round(float(x), 6) for x in q],
        }
    return poses


def norm_object(name: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return OBJECT_ALIASES.get(clean, clean or "unknown_object")


def relation_type(text: str) -> str:
    low = text.lower()
    if any(word in low for word in ("grasp", "hold", "holding", "pick up", "pickup")):
        return "hand_grasps"
    if any(word in low for word in ("pour", "tilt")):
        return "hand_pours_with"
    if any(word in low for word in ("touch", "contact", "place", "position")):
        return "hand_contacts"
    if any(word in low for word in ("move", "moving", "reach")):
        return "hand_moves_toward"
    return "hand_interacts_with"


def frame_records_from_caption(caption: dict, max_frames: int | None) -> list[dict]:
    frames_by_ts: dict[str, dict] = {}
    for segment in caption.get("segments", []):
        segment_id = int(segment.get("segment_id", -1))
        subtask = segment.get("Sub Task", "")
        objects = segment.get("objects", {}) or {}
        interactions = segment.get("interaction", {}) or {}
        sampled = segment.get("sampled_frames", {}) or {}
        timestamps = sorted({str(v) for v in sampled.values()} | set(map(str, objects.keys())) | set(map(str, interactions.keys())), key=int)
        for ts in timestamps:
            frame = frames_by_ts.setdefault(ts, {"timestamp": ts, "segment_id": segment_id, "subtask": subtask, "objects": [], "interaction_text": ""})
            if ts in objects:
                frame["objects"] = sorted(set(frame["objects"]) | set(map(str, objects[ts])))
            if ts in interactions:
                frame["interaction_text"] = str(interactions[ts])
            frame["action"] = active_action(segment, int(ts))
    frames = [frames_by_ts[k] for k in sorted(frames_by_ts.keys(), key=int)]
    if max_frames:
        frames = frames[:max_frames]
    return frames


def active_action(segment: dict, timestamp: int) -> str:
    for action in segment.get("Current Action", []):
        start = int(action.get("start_frame", 0))
        end = int(action.get("end_frame", 0))
        if start <= timestamp <= end:
            return str(action.get("label", ""))
    return ""


def segment_records(caption: dict) -> list[dict]:
    rows = []
    for segment in caption.get("segments", []):
        actions = []
        for action in segment.get("Current Action", []):
            actions.append({
                "label": action.get("label", ""),
                "description": action.get("description", ""),
                "start_timestamp": str(action.get("start_frame", "")),
                "end_timestamp": str(action.get("end_frame", "")),
            })
        rows.append({
            "segment_id": int(segment.get("segment_id", -1)),
            "subtask": segment.get("Sub Task", ""),
            "start_timestamp": str(segment.get("start_frame", "")),
            "end_timestamp": str(segment.get("end_frame", "")),
            "actions": actions,
        })
    return rows


def detector_records_by_timestamp(detections_json: Path | None, frames: list[dict]) -> dict[str, list[dict]]:
    if detections_json is None:
        return {}
    payload = json.loads(detections_json.read_text(encoding="utf-8"))
    rows = payload.get("detections", payload) if isinstance(payload, dict) else payload
    by_ts: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        timestamp = row.get("timestamp")
        if timestamp is None and "frame_index" in row:
            idx = int(row["frame_index"])
            if 0 <= idx < len(frames):
                timestamp = frames[idx]["timestamp"]
        if timestamp is None:
            continue
        objects = row.get("objects", row.get("detections", []))
        for item in objects:
            label = str(item.get("label", item.get("name", ""))).strip()
            if not label:
                continue
            by_ts[str(timestamp)].append({
                "name": label,
                "track_id": item.get("track_id"),
                "confidence": float(item.get("confidence", row.get("confidence", 0.5))),
                "bbox_xyxy": item.get("bbox_xyxy", item.get("bbox")),
                "provenance": "detector.tracker_json",
            })
    return by_ts


def merge_detector_records(frames: list[dict], detections_by_ts: dict[str, list[dict]]) -> list[dict]:
    for frame in frames:
        sources = {norm_object(name): {"caption.objects"} for name in frame.get("objects", [])}
        dets = detections_by_ts.get(frame["timestamp"], [])
        for det in dets:
            sources.setdefault(norm_object(det["name"]), set()).add("detector.tracker_json")
        frame["object_sources"] = {name: sorted(values) for name, values in sources.items()}
        if not dets:
            continue
        frame["detector_objects"] = dets
        labels = [det["name"] for det in dets]
        frame["objects"] = sorted(set(frame.get("objects", [])) | set(labels))
    return frames


def build_scene_graph(data_root: Path, max_frames: int | None, detections_json: Path | None = None) -> dict:
    annotation = data_root / "annotation.hdf5"
    caption = load_caption(annotation)
    poses = load_slam_pose_preview(annotation)
    frames = frame_records_from_caption(caption, max_frames)
    detections_by_ts = detector_records_by_timestamp(detections_json, frames)
    frames = merge_detector_records(frames, detections_by_ts)
    objects: dict[str, dict] = {}
    relations = []
    object_counts = Counter()

    for frame_idx, frame in enumerate(frames):
        ts = frame["timestamp"]
        frame["camera_pose"] = poses.get(ts)
        detector_by_id = {norm_object(row["name"]): row for row in frame.get("detector_objects", [])}
        seen_frame_objects = set()
        for obj_name in frame["objects"]:
            obj_id = norm_object(obj_name)
            if obj_id in seen_frame_objects:
                if obj_id in objects:
                    objects[obj_id]["aliases"] = sorted(set(objects[obj_id]["aliases"]) | {obj_name})
                continue
            seen_frame_objects.add(obj_id)
            detector_hit = detector_by_id.get(obj_id)
            provenance = "+".join(frame.get("object_sources", {}).get(obj_id, ["caption.objects"]))
            object_counts[obj_id] += 1
            record = objects.setdefault(obj_id, {
                "name": obj_name,
                "aliases": sorted({obj_name}),
                "first_seen": ts,
                "last_seen": ts,
                "observations": 0,
                "provenance": provenance,
            })
            record["last_seen"] = ts
            record["observations"] += 1
            record["aliases"] = sorted(set(record["aliases"]) | {obj_name})
            if detector_hit and detector_hit.get("track_id") is not None:
                record["track_ids"] = sorted(set(record.get("track_ids", [])) | {str(detector_hit["track_id"])})
            relations.append({
                "type": "visible_in",
                "subject": obj_id,
                "object": f"frame:{frame_idx}",
                "timestamp": ts,
                "confidence": float(detector_hit.get("confidence", 0.85)) if detector_hit else 0.85,
                "provenance": provenance,
            })
        text = frame.get("interaction_text", "")
        low = text.lower()
        for obj_name in frame["objects"]:
            obj_id = norm_object(obj_name)
            if obj_name.lower() in low or obj_id.replace("_", " ") in low:
                relations.append({
                    "type": relation_type(text),
                    "subject": "hand",
                    "object": obj_id,
                    "timestamp": ts,
                    "segment_id": frame["segment_id"],
                    "text": text,
                    "confidence": 0.65,
                    "provenance": "caption.interaction_text+object_match",
                })
        if frame.get("action"):
            relations.append({
                "type": "action_active",
                "subject": "person",
                "object": frame["action"],
                "timestamp": ts,
                "segment_id": frame["segment_id"],
                "confidence": 0.75,
                "provenance": "caption.current_action",
            })

    return {
        "metadata": {
            "main_task": caption.get("config", {}).get("Main Task", ""),
            "source_data_root": str(data_root),
            "num_frames": len(frames),
            "num_objects": len(objects),
            "num_relations": len(relations),
            "top_objects": object_counts.most_common(10),
        },
        "frames": frames,
        "objects": objects,
        "relations": relations,
        "segments": segment_records(caption),
        "provenance": {
            "objects": "Caption object annotations in annotation.hdf5.",
            "relations": "Rule-based extraction from object lists, interaction text, and action intervals.",
            "camera_pose": "SLAM trans_xyz and quat_wxyz matched by timestamp when present.",
            "detector_hook": "Optional --detections-json merges detector/tracker object records with caption objects.",
        },
    }


def query_object(graph: dict, object_id: str) -> dict:
    oid = norm_object(object_id)
    hits = [rel for rel in graph["relations"] if rel.get("subject") == oid or rel.get("object") == oid]
    frames = [frame for frame in graph["frames"] if oid in [norm_object(x) for x in frame.get("objects", [])]]
    return {"query": f"object:{object_id}", "object": graph["objects"].get(oid), "timeline": frames, "relations": hits}


def query_interactions(graph: dict) -> dict:
    hits = [rel for rel in graph["relations"] if rel["type"].startswith("hand_")]
    by_object = defaultdict(int)
    for rel in hits:
        by_object[rel["object"]] += 1
    return {"query": "interactions", "count": len(hits), "by_object": dict(sorted(by_object.items())), "relations": hits}


def query_state(graph: dict, timestamp: str) -> dict:
    if timestamp == "last":
        frame = graph["frames"][-1]
    else:
        ts = int(timestamp)
        frame = min(graph["frames"], key=lambda row: abs(int(row["timestamp"]) - ts))
    visible = [norm_object(x) for x in frame.get("objects", [])]
    active = [rel for rel in graph["relations"] if rel["timestamp"] == frame["timestamp"] and rel["type"] in ("action_active", "hand_grasps", "hand_contacts", "hand_pours_with", "hand_interacts_with")]
    return {"query": f"state:{timestamp}", "timestamp": frame["timestamp"], "subtask": frame.get("subtask"), "action": frame.get("action"), "visible_objects": visible, "active_relations": active}


def run_query(graph: dict, query: str) -> dict:
    if query.startswith("object:"):
        return query_object(graph, query.split(":", 1)[1])
    if query == "interactions":
        return query_interactions(graph)
    if query.startswith("state:"):
        return query_state(graph, query.split(":", 1)[1])
    raise ValueError(f"Unknown query: {query}")


def parse_args() -> argparse.Namespace:
    root_default = Path(__file__).resolve().parents[2] / "data/sample/xperience-10m-sample"
    parser = argparse.ArgumentParser(description="Export and query a temporal scene graph from an egocentric Xperience sample.")
    parser.add_argument("--data-root", type=Path, default=root_default)
    parser.add_argument("--graph-json", type=Path, help="Query an existing scene_graph.json without requiring raw data.")
    parser.add_argument("--detections-json", type=Path, help="Optional detector/tracker JSON with timestamped objects to merge into the graph.")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/sample_graph"))
    parser.add_argument("--max-frames", type=int, default=80)
    parser.add_argument("--query", action="append", default=["object:kettle", "interactions", "state:last"], help="Query: object:<name>, interactions, or state:<timestamp|last>.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if args.graph_json:
        graph = json.loads(args.graph_json.read_text(encoding="utf-8"))
    else:
        graph = build_scene_graph(args.data_root, None if args.max_frames == 0 else args.max_frames, args.detections_json)
        (args.output_dir / "scene_graph.json").write_text(json.dumps(graph, indent=2), encoding="utf-8")
    results = [run_query(graph, query) for query in args.query]
    (args.output_dir / "query_results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (args.output_dir / "schema.json").write_text(json.dumps(SCHEMA, indent=2), encoding="utf-8")
    print(f"frames={graph['metadata']['num_frames']} objects={graph['metadata']['num_objects']} relations={graph['metadata']['num_relations']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
