#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def frame_boxes(frame, max_boxes: int) -> list[list[int]]:
    import cv2

    small = cv2.resize(frame, (640, 360), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 60, 140)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < 800 or w < 24 or h < 24:
            continue
        boxes.append((area, [int(x), int(y), int(x + w), int(y + h)]))
    if not boxes:
        h, w = small.shape[:2]
        boxes = [(w * h, [int(w * 0.25), int(h * 0.2), int(w * 0.75), int(h * 0.8)])]
    boxes.sort(reverse=True, key=lambda item: item[0])
    return [box for _area, box in boxes[:max_boxes]]


def generate(graph: dict, video_path: Path, max_frames: int, stride: int) -> dict:
    import cv2

    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")
    detections = []
    try:
        for frame_idx, graph_frame in enumerate(graph.get("frames", [])[:max_frames]):
            source_frame = frame_idx * stride
            cap.set(cv2.CAP_PROP_POS_FRAMES, source_frame)
            ok, frame = cap.read()
            if not ok:
                break
            labels = graph_frame.get("objects", [])
            boxes = frame_boxes(frame, max(1, len(labels)))
            objects = []
            for object_idx, label in enumerate(labels):
                box = boxes[min(object_idx, len(boxes) - 1)]
                objects.append({
                    "label": label,
                    "track_id": f"visual-{label.lower().replace(' ', '_')}-{object_idx}",
                    "confidence": round(0.62 + min(0.28, 0.03 * object_idx), 2),
                    "bbox_xyxy": box,
                })
            detections.append({"timestamp": graph_frame["timestamp"], "frame_index": frame_idx, "source_frame": source_frame, "objects": objects})
    finally:
        cap.release()
    return {
        "source": "OpenCV contour proposals associated with graph-visible object labels",
        "video_path": str(video_path),
        "stride": stride,
        "detections": detections,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate detector/tracker-style JSON from real video frames using OpenCV visual proposals.")
    parser.add_argument("--graph-json", type=Path, default=Path("outputs/sample_graph/scene_graph.json"))
    parser.add_argument("--video", type=Path, default=Path("../data/sample/xperience-10m-sample/fisheye_cam0.mp4"))
    parser.add_argument("--output-json", type=Path, default=Path("docs/data/visual_detections.json"))
    parser.add_argument("--max-frames", type=int, default=24)
    parser.add_argument("--stride", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    graph = json.loads(args.graph_json.read_text(encoding="utf-8"))
    payload = generate(graph, args.video, args.max_frames, args.stride)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"detections={len(payload['detections'])} output={args.output_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
