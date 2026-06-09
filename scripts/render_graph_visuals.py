#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def render(graph_path: Path, output_path: Path) -> None:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    top = graph["metadata"]["top_objects"][:6]
    max_count = max((count for _name, count in top), default=1)
    rows = []
    y = 104
    for name, count in top:
        width = int(360 * count / max_count)
        rows.append(f"""
    <text x="78" y="{y - 8}" fill="#cbd5e1" font-size="15" font-family="Inter, Arial">{name}</text>
    <rect x="78" y="{y}" width="360" height="18" rx="9" fill="#0f172a" stroke="#334155"/>
    <rect x="78" y="{y}" width="{width}" height="18" rx="9" fill="#22d3ee"/>
    <text x="456" y="{y + 15}" fill="#e2e8f0" font-size="15" font-family="Inter, Arial">{count}</text>
""")
        y += 38
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="760" height="360" viewBox="0 0 760 360">
  <rect width="760" height="360" rx="28" fill="#020617"/>
  <text x="48" y="48" fill="#f8fafc" font-size="26" font-weight="700" font-family="Inter, Arial">Top Object Memories</text>
  <text x="48" y="76" fill="#94a3b8" font-size="15" font-family="Inter, Arial">{graph['metadata']['num_frames']} frames · {graph['metadata']['num_objects']} canonical objects · {graph['metadata']['num_relations']} relations</text>
  {''.join(rows)}
  <text x="48" y="326" fill="#64748b" font-size="13" font-family="Inter, Arial">Counts reflect object observations after alias merging.</text>
</svg>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")


def render_timeline(graph_path: Path, output_path: Path) -> None:
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    frames = graph["frames"][:12]
    if not frames:
        return
    ticks = []
    for idx, frame in enumerate(frames):
        x = 70 + idx * 54
        label = (frame.get("action") or frame.get("subtask") or "frame")[:14]
        obj_count = len(frame.get("objects", []))
        ticks.append(f'<circle cx="{x}" cy="150" r="{6 + min(obj_count, 8)}" fill="#22d3ee" opacity=".85"/>')
        ticks.append(f'<text x="{x}" y="188" fill="#94a3b8" font-family="Inter,Arial" font-size="10" text-anchor="middle">{idx}</text>')
        ticks.append(f'<text x="{x}" y="210" fill="#cbd5e1" font-family="Inter,Arial" font-size="10" text-anchor="middle">{label}</text>')
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="760" height="300" viewBox="0 0 760 300">
  <rect width="760" height="300" rx="28" fill="#020617"/>
  <text x="48" y="48" fill="#f8fafc" font-size="26" font-weight="700" font-family="Inter, Arial">Scene Graph Timeline</text>
  <text x="48" y="76" fill="#94a3b8" font-size="15" font-family="Inter, Arial">First 12 sampled frames · bubble size reflects visible object count</text>
  <path d="M70 150 H664" stroke="#334155" stroke-width="4" stroke-linecap="round"/>
  {''.join(ticks)}
</svg>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")


def main() -> int:
    render(Path("outputs/sample_graph/scene_graph.json"), Path("docs/assets/top_objects.svg"))
    render_timeline(Path("outputs/sample_graph/scene_graph.json"), Path("docs/assets/graph_timeline.svg"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
