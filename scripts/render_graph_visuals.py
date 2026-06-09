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


def main() -> int:
    render(Path("outputs/sample_graph/scene_graph.json"), Path("docs/assets/top_objects.svg"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
