#!/usr/bin/env python3
"""Evaluate a scene graph against human-labeled QA pairs.

The gold answers in eval/qa_pairs.json were written by reading the episode,
so this measures whether graph construction and query logic preserve what a
human can check: object memory, alias handling, interactions, task state, and
the egocentric position proxy. It is a regression benchmark for the graph
builder, not a perception benchmark.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import defaultdict
from pathlib import Path

from scene_graph_demo import norm_object, query_state


def answer_object_in_memory(graph: dict, question: dict):
    return norm_object(question["object"]) in graph["objects"]


def answer_object_visible_at(graph: dict, question: dict):
    oid = norm_object(question["object"])
    ts = str(question["timestamp"])
    for frame in graph["frames"]:
        if frame["timestamp"] == ts:
            return oid in [norm_object(x) for x in frame.get("objects", [])]
    return False


def answer_interaction_occurs(graph: dict, question: dict):
    oid = norm_object(question["object"])
    wanted = question.get("relation")
    for rel in graph["relations"]:
        if rel.get("object") != oid or not rel["type"].startswith("hand_"):
            continue
        if wanted is None or rel["type"] == wanted:
            return True
    return False


def answer_subtask_at(graph: dict, question: dict):
    return query_state(graph, str(question["timestamp"])).get("subtask")


def answer_action_at(graph: dict, question: dict):
    return query_state(graph, str(question["timestamp"])).get("action")


def answer_first_seen_before(graph: dict, question: dict):
    a = graph["objects"].get(norm_object(question["object_a"]))
    b = graph["objects"].get(norm_object(question["object_b"]))
    if a is None or b is None:
        return None
    return int(a["first_seen"]) < int(b["first_seen"])


def answer_last_seen_near(graph: dict, question: dict):
    record = graph["objects"].get(norm_object(question["object"]))
    position = (record or {}).get("last_seen_camera_xyz")
    if position is None:
        return False
    expected = question["camera_xyz"]
    tolerance = float(question.get("tolerance", 0.25))
    distance = math.dist([float(x) for x in position], [float(x) for x in expected])
    return distance <= tolerance


ANSWERERS = {
    "object_in_memory": answer_object_in_memory,
    "object_visible_at": answer_object_visible_at,
    "interaction_occurs": answer_interaction_occurs,
    "subtask_at": answer_subtask_at,
    "action_at": answer_action_at,
    "first_seen_before": answer_first_seen_before,
    "last_seen_near": answer_last_seen_near,
}


def evaluate(graph: dict, questions: list[dict]) -> dict:
    rows = []
    per_type = defaultdict(lambda: {"correct": 0, "total": 0})
    for question in questions:
        qtype = question["type"]
        answerer = ANSWERERS.get(qtype)
        if answerer is None:
            raise ValueError(f"Unknown question type: {qtype}")
        predicted = answerer(graph, question)
        correct = predicted == question["answer"]
        per_type[qtype]["total"] += 1
        per_type[qtype]["correct"] += int(correct)
        rows.append({**question, "predicted": predicted, "correct": correct})
    total = len(rows)
    n_correct = sum(row["correct"] for row in rows)
    return {
        "num_questions": total,
        "num_correct": n_correct,
        "accuracy": n_correct / total if total else 0.0,
        "per_type": {
            qtype: {**counts, "accuracy": counts["correct"] / counts["total"]}
            for qtype, counts in sorted(per_type.items())
        },
        "results": rows,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Score a scene graph against human-labeled QA pairs.")
    parser.add_argument("--graph-json", type=Path, default=Path("outputs/sample_graph/scene_graph.json"))
    parser.add_argument("--qa-json", type=Path, default=Path("eval/qa_pairs.json"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/qa_eval"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    graph = json.loads(args.graph_json.read_text(encoding="utf-8"))
    questions = json.loads(args.qa_json.read_text(encoding="utf-8"))["questions"]
    report = evaluate(graph, questions)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "qa_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"qa accuracy: {report['num_correct']}/{report['num_questions']} = {report['accuracy']:.3f}")
    for qtype, counts in report["per_type"].items():
        print(f"  {qtype}: {counts['correct']}/{counts['total']}")
    failures = [row for row in report["results"] if not row["correct"]]
    for row in failures[:10]:
        print(f"  MISS {row['type']}: expected {row['answer']!r} got {row['predicted']!r} ({row.get('text', '')})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
