"""MicroCount analysis helpers: turn simple feature checkboxes into a runnable
pipeline config, and read a capture date from each image for auto-organization.

This is the no-code path: the user ticks "cell count" / "intensity" and we
assemble the standard detect→measure graph the existing engine already runs.
"""
from __future__ import annotations

import datetime as dt
import os
from pathlib import Path

from PIL import Image

# Features the MVP exposes as checkboxes.
FEATURE_CELL_COUNT = "cell_count"
FEATURE_INTENSITY = "intensity"
SUPPORTED_FEATURES = {FEATURE_CELL_COUNT, FEATURE_INTENSITY}

_EXIF_DATETIME_ORIGINAL = 36867
_EXIF_DATETIME = 306


def build_config(features: set[str], channel: str = "green") -> dict:
    """Assemble a pipeline graph from the selected features.

    Both cell counting and intensity rely on detection + per-region stats, so a
    measurement node is included whenever either feature is requested (the cell
    count is the number of detected regions)."""
    nodes = [
        {"id": "load", "type": "image_load", "params": {}},
        {
            "id": "prep",
            "type": "preprocessing",
            "params": {"blur_kernel": 3, "normalize": True},
        },
        {"id": "thresh", "type": "thresholding", "params": {"method": "otsu"}},
        {"id": "detect", "type": "cell_detection", "params": {"model_type": "cyto"}},
    ]
    edges = [("load", "prep"), ("prep", "thresh"), ("thresh", "detect")]
    last = "detect"

    if features & {FEATURE_CELL_COUNT, FEATURE_INTENSITY}:
        nodes.append(
            {
                "id": "measure",
                "type": "intensity_measurement",
                "params": {"channel": channel},
            }
        )
        edges.append((last, "measure"))
        last = "measure"

    nodes.append(
        {
            "id": "export",
            "type": "export_results",
            "params": {"include_images": True},
        }
    )
    edges.append((last, "export"))

    return {
        "nodes": nodes,
        "edges": [{"source": s, "target": t} for s, t in edges],
    }


def capture_date(path: str | Path) -> str:
    """Return an ISO date (YYYY-MM-DD) for an image: EXIF capture time when
    present, otherwise the file's modification date."""
    path = Path(path)
    try:
        with Image.open(path) as im:
            exif = im.getexif()
            for tag in (_EXIF_DATETIME_ORIGINAL, _EXIF_DATETIME):
                value = exif.get(tag)
                if value:
                    # EXIF format: "YYYY:MM:DD HH:MM:SS"
                    return str(value)[:10].replace(":", "-")
    except Exception:  # noqa: BLE001 - any decode issue falls back to mtime
        pass
    return dt.date.fromtimestamp(os.path.getmtime(path)).isoformat()
