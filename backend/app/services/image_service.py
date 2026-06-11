"""Pipeline execution: load an image, run the module graph, return metrics."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageDraw

from ..utils.image_processing import MODULE_FUNCS, to_gray
from ..utils.validators import is_image_file

logger = logging.getLogger("image_service")

_OUTLINE = (255, 230, 0)  # yellow cell outlines
_MARKER = (255, 60, 60)  # red centroid dots


def load_image(path: str | Path) -> np.ndarray:
    """Load an image preserving its bit depth and channels.

    Microscopy images are routinely 16-bit; downcasting to 8-bit would corrupt
    the intensity values we measure. So we keep the native dtype (uint16/int32/
    float) and only normalize modes numpy can't represent directly (palette,
    alpha).
    """
    with Image.open(path) as im:
        mode = im.mode
        if mode == "P":  # palette index -> RGB
            return np.asarray(im.convert("RGB"))
        if mode in ("RGBA", "LA"):  # drop alpha
            return np.asarray(im.convert("RGB" if mode == "RGBA" else "L"))
        if mode.startswith("I;16"):  # 16-bit grayscale (common for microscopy)
            return np.asarray(im, dtype=np.uint16)
        if mode == "I":  # 32-bit integer grayscale
            return np.asarray(im, dtype=np.int32)
        return np.asarray(im)


def _to_rgb_uint8(arr: np.ndarray) -> np.ndarray:
    """Coerce any image array to a contiguous (H, W, 3) uint8 array."""
    a = np.asarray(arr)
    if a.ndim == 2:
        a = np.stack([a] * 3, axis=-1)
    elif a.ndim == 3 and a.shape[2] >= 3:
        a = a[..., :3]
    else:
        a = np.stack([to_gray(a)] * 3, axis=-1)
    return np.ascontiguousarray(np.clip(a, 0, 255).astype(np.uint8))


def render_overlay(
    original: np.ndarray, labels: np.ndarray, cells: list[dict] | None = None
) -> Image.Image:
    """Draw detected-cell outlines (and centroid markers) over the original
    image so users can see what was segmented, not just the numbers."""
    rgb = _to_rgb_uint8(original)

    # Boundary = pixels where the label differs from a 4-neighbour.
    lab = np.asarray(labels)
    boundary = np.zeros(lab.shape, dtype=bool)
    boundary[:-1, :] |= lab[:-1, :] != lab[1:, :]
    boundary[1:, :] |= lab[:-1, :] != lab[1:, :]
    boundary[:, :-1] |= lab[:, :-1] != lab[:, 1:]
    boundary[:, 1:] |= lab[:, :-1] != lab[:, 1:]
    boundary &= lab > 0  # keep the cell side of each edge only

    rgb[boundary] = _OUTLINE
    img = Image.fromarray(rgb, mode="RGB")

    # Mark centroids of the larger cells so dense fields stay readable.
    if cells:
        draw = ImageDraw.Draw(img)
        for c in sorted(cells, key=lambda c: c.get("area", 0), reverse=True)[:60]:
            x, y = c.get("centroid_x"), c.get("centroid_y")
            if x is None or y is None:
                continue
            draw.ellipse([x - 2, y - 2, x + 2, y + 2], fill=_MARKER)
    return img


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

    # Confluence / % area coverage (ImageJ "Area Fraction").
    labels = ctx.get("labels")
    mask = ctx.get("mask")
    covered = None
    if labels is not None:
        covered = int((labels > 0).sum())
        total_px = int(labels.size)
    elif mask is not None:
        covered = int(np.asarray(mask).sum())
        total_px = int(np.asarray(mask).size)
    if covered is not None:
        aggregate.setdefault("percent_area", round(100.0 * covered / total_px, 3))

    if cells:
        aggregate.setdefault(
            "mean_cell_intensity",
            round(float(np.mean([c["mean_intensity"] for c in cells])), 4),
        )
        aggregate.setdefault(
            "total_area", int(sum(c["area"] for c in cells))
        )

    overlay = None
    if "labels" in ctx:
        try:
            overlay = render_overlay(ctx.get("original", img), ctx["labels"], cells)
        except Exception:  # noqa: BLE001 - never fail a job over a preview image
            logger.exception("overlay rendering failed")

    return {
        "rows": cells,
        "aggregate": aggregate,
        "include_images": ctx.get("include_images", False),
        "overlay": overlay,
    }


def list_images(folder: str | Path) -> list[Path]:
    folder = Path(folder)
    if not folder.exists():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and is_image_file(p.name))
