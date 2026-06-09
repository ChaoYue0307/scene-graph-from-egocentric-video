from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from scene_graph_demo import frame_records_from_caption, norm_object, query_object, relation_type, run_query  # noqa: E402


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
