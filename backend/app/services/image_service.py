"""Pipeline execution: load an image, run the module graph, return metrics."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from ..utils.image_processing import MODULE_FUNCS
from ..utils.validators import is_image_file

logger = logging.getLogger("image_service")


def load_image(path: str | Path) -> np.ndarray:
    """Load an image file into an (H, W) or (H, W, C) numpy array."""
    with Image.open(path) as im:
        im = im.convert("RGB") if im.mode not in ("L", "RGB") else im
        return np.asarray(im)


def topo_order(nodes: list[dict], edges: list[dict]) -> list[dict]:
    """Return nodes in execution order (Kahn's algorithm). Falls back to input
    order for disconnected graphs."""
    by_id = {n["id"]: n for n in nodes}
    indeg = {n["id"]: 0 for n in nodes}
    adj: dict[str, list[str]] = {n["id"]: [] for n in nodes}
    for e in edges:
        if e["source"] in by_id and e["target"] in by_id:
            adj[e["source"]].append(e["target"])
            indeg[e["target"]] += 1

    queue = [nid for nid, d in indeg.items() if d == 0]
    ordered: list[str] = []
    while queue:
        nid = queue.pop(0)
        ordered.append(nid)
        for m in adj[nid]:
            indeg[m] -= 1
            if indeg[m] == 0:
                queue.append(m)

    # append any nodes left out (cycles/disconnected), preserving input order
    seen = set(ordered)
    ordered.extend(n["id"] for n in nodes if n["id"] not in seen)
    return [by_id[nid] for nid in ordered]


def run_pipeline_on_image(image_path: str | Path, config: dict) -> dict[str, Any]:
    """Execute the pipeline for a single image.

    Returns a dict with per-cell ``rows`` and image-level ``aggregate`` metrics.
    """
    img = load_image(image_path)
    ctx: dict[str, Any] = {"image": img.astype(np.float64), "original": img}

    nodes = config.get("nodes", [])
    edges = config.get("edges", [])
    for node in topo_order(nodes, edges):
        fn = MODULE_FUNCS.get(node["type"])
        if fn is None:
            logger.warning("skipping unknown module type: %s", node.get("type"))
            continue
        ctx = fn(ctx, node.get("params", {}) or {})

    cells = ctx.get("cells", [])
    aggregate = ctx.get("aggregate", {})
    aggregate.setdefault("cell_count", len(cells))
    if cells:
        aggregate.setdefault(
            "mean_cell_intensity",
            round(float(np.mean([c["mean_intensity"] for c in cells])), 4),
        )
        aggregate.setdefault(
            "total_area", int(sum(c["area"] for c in cells))
        )

    return {
        "rows": cells,
        "aggregate": aggregate,
        "include_images": ctx.get("include_images", False),
    }


def list_images(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and is_image_file(p.name))
