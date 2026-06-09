from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol


class CaptionSource(Protocol):
    """Provides frame-level objects, interactions, and action intervals."""

    annotation_path: Path


class DetectionSource(Protocol):
    """Provides optional detector or tracker records for graph construction."""

    detections_path: Path | None


@dataclass(frozen=True)
class XperienceSceneGraphAdapter:
    """Boundary object for the Xperience-10M scene graph sample layout."""

    data_root: Path
    detections_path: Path | None = None

    @property
    def annotation_path(self) -> Path:
        return self.data_root / "annotation.hdf5"

    def describe(self) -> dict:
        return {
            "adapter": "XperienceSceneGraphAdapter",
            "annotation_path": str(self.annotation_path),
            "detections_path": str(self.detections_path) if self.detections_path else None,
            "signals": ["caption_objects", "interaction_text", "action_intervals", "optional_detector_tracks"],
        }
