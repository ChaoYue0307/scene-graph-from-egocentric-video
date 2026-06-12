from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from adapters import XperienceSceneGraphAdapter  # noqa: E402
from evaluate_graph_qa import evaluate  # noqa: E402
from scene_graph_demo import compare_graphs, detector_records_by_timestamp, frame_records_from_caption, main, merge_detector_records, norm_object, query_object, query_where, relation_type, run_query  # noqa: E402


def test_norm_object_merges_aliases() -> None:
    assert norm_object("gooseneck kettle") == "kettle"
    assert norm_object("digital scale") == "scale"
    assert norm_object("coffee dripper") == "dripper"


def test_relation_type_from_text() -> None:
    assert relation_type("Hand is grasping the kettle") == "hand_grasps"
    assert relation_type("hand pouring water") == "hand_pours_with"
    assert relation_type("hand moving toward mug") == "hand_moves_toward"


def test_frame_records_from_caption() -> None:
    caption = {
        "segments": [
            {
                "segment_id": 0,
                "Sub Task": "Pick up kettle",
                "sampled_frames": {"Image 1": 10},
                "objects": {"10": ["gooseneck kettle"]},
                "interaction": {"10": "Hand is grasping the kettle."},
                "Current Action": [{"label": "Pick up kettle", "start_frame": 1, "end_frame": 20}],
            }
        ]
    }
    frames = frame_records_from_caption(caption, None)
    assert frames[0]["timestamp"] == "10"
    assert frames[0]["action"] == "Pick up kettle"


def test_query_object_uses_canonical_id() -> None:
    graph = {
        "objects": {"kettle": {"name": "gooseneck kettle"}},
        "frames": [{"objects": ["gooseneck kettle"], "timestamp": "10"}],
        "relations": [{"type": "visible_in", "subject": "kettle", "object": "frame:0", "timestamp": "10"}],
    }
    result = query_object(graph, "gooseneck kettle")
    assert result["object"]["name"] == "gooseneck kettle"
    assert len(result["timeline"]) == 1


def test_run_query_rejects_unknown_query() -> None:
    try:
        run_query({"frames": [], "relations": [], "objects": {}}, "unknown")
    except ValueError as exc:
        assert "Unknown query" in str(exc)
    else:
        raise AssertionError("Expected ValueError")


def _memory_graph() -> dict:
    return {
        "objects": {
            "kettle": {
                "name": "kettle",
                "first_seen": "10",
                "last_seen": "30",
                "last_seen_camera_xyz": [0.1, 0.2, 0.3],
                "camera_trail": [
                    {"timestamp": "10", "camera_xyz": [0.0, 0.0, 0.0]},
                    {"timestamp": "30", "camera_xyz": [0.1, 0.2, 0.3]},
                ],
            },
            "scale": {"name": "scale", "first_seen": "20", "last_seen": "20"},
        },
        "frames": [
            {"timestamp": "10", "objects": ["kettle"], "subtask": "pick", "action": "Pick up kettle"},
            {"timestamp": "30", "objects": ["kettle", "scale"], "subtask": "pour", "action": ""},
        ],
        "relations": [
            {"type": "hand_grasps", "subject": "hand", "object": "kettle", "timestamp": "10"},
            {"type": "visible_in", "subject": "scale", "object": "frame:1", "timestamp": "30"},
        ],
    }


def test_query_where_returns_egocentric_position_memory() -> None:
    result = query_where(_memory_graph(), "gooseneck kettle")
    assert result["found"] is True
    assert result["last_seen_camera_xyz"] == [0.1, 0.2, 0.3]
    assert result["sightings_with_pose"] == 2
    missing = query_where(_memory_graph(), "microwave")
    assert missing["found"] is False


def test_qa_evaluate_scores_all_question_types() -> None:
    graph = _memory_graph()
    questions = [
        {"type": "object_in_memory", "object": "digital scale", "answer": True},
        {"type": "object_in_memory", "object": "laptop", "answer": False},
        {"type": "object_visible_at", "object": "kettle", "timestamp": "10", "answer": True},
        {"type": "interaction_occurs", "object": "kettle", "relation": "hand_grasps", "answer": True},
        {"type": "interaction_occurs", "object": "scale", "answer": False},
        {"type": "subtask_at", "timestamp": "10", "answer": "pick"},
        {"type": "action_at", "timestamp": "30", "answer": ""},
        {"type": "first_seen_before", "object_a": "kettle", "object_b": "scale", "answer": True},
        {"type": "last_seen_near", "object": "kettle", "camera_xyz": [0.1, 0.2, 0.3], "tolerance": 0.05, "answer": True},
        {"type": "last_seen_near", "object": "scale", "camera_xyz": [0.0, 0.0, 0.0], "answer": False},
    ]
    report = evaluate(graph, questions)
    assert report["num_questions"] == 10
    assert report["accuracy"] == 1.0
    assert report["per_type"]["object_in_memory"]["correct"] == 2


def test_qa_evaluate_detects_wrong_answers() -> None:
    report = evaluate(_memory_graph(), [{"type": "object_in_memory", "object": "kettle", "answer": False}])
    assert report["accuracy"] == 0.0
    assert report["results"][0]["predicted"] is True


def test_cli_query_existing_graph(tmp_path: Path, monkeypatch) -> None:
    graph_path = tmp_path / "scene_graph.json"
    graph_path.write_text(
        '{"metadata":{"num_frames":1,"num_objects":1,"num_relations":1},'
        '"objects":{"kettle":{"name":"kettle"}},'
        '"frames":[{"timestamp":"10","objects":["kettle"],"subtask":"demo","action":"move"}],'
        '"relations":[{"type":"visible_in","subject":"kettle","object":"frame:0","timestamp":"10"}]}',
        encoding="utf-8",
    )
    out_dir = tmp_path / "out"
    monkeypatch.setattr(
        "sys.argv",
        ["scene_graph_demo.py", "--graph-json", str(graph_path), "--output-dir", str(out_dir), "--query", "object:kettle"],
    )
    assert main() == 0
    assert (out_dir / "query_results.json").exists()
    assert not (out_dir / "scene_graph.json").exists()


def test_detector_records_merge_by_frame_index(tmp_path: Path) -> None:
    frames = [{"timestamp": "100", "objects": ["kettle"]}, {"timestamp": "200", "objects": []}]
    detections = tmp_path / "detections.json"
    detections.write_text(
        '{"detections":[{"frame_index":1,"objects":[{"label":"mug","track_id":"t1","confidence":0.9,"bbox_xyxy":[1,2,3,4]}]}]}',
        encoding="utf-8",
    )
    by_ts = detector_records_by_timestamp(detections, frames)
    merged = merge_detector_records(frames, by_ts)
    assert merged[1]["objects"] == ["mug"]
    assert merged[1]["object_sources"]["mug"] == ["detector.tracker_json"]
    assert merged[1]["detector_objects"][0]["track_id"] == "t1"


def test_xperience_scene_graph_adapter_paths(tmp_path: Path) -> None:
    detections = tmp_path / "detections.json"
    adapter = XperienceSceneGraphAdapter(tmp_path, detections)
    assert adapter.annotation_path == tmp_path / "annotation.hdf5"
    assert adapter.describe()["detections_path"] == str(detections)
    assert "optional_detector_tracks" in adapter.describe()["signals"]


def test_compare_graphs_counts_added_detector_objects() -> None:
    base = {"objects": {"kettle": {}}, "relations": [{"type": "visible_in"}]}
    candidate = {
        "objects": {"kettle": {}, "mug": {}},
        "relations": [
            {"type": "visible_in"},
            {"type": "visible_in", "provenance": "detector.tracker_json"},
        ],
    }
    comparison = compare_graphs(base, candidate)
    assert comparison["added_objects"] == ["mug"]
    assert comparison["detector_relation_count"] == 1
