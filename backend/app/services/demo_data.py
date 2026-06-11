"""Synthetic microscopy image generation for demos and tests.

Produces fluorescence-style images (dark background with bright, roughly
circular "cells") using only numpy + Pillow, so it works in minimal
environments without OpenCV/scikit-image. The output is deterministic per
``seed`` so demo runs are reproducible.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

# Keep these modest so a demo job finishes in seconds.
DEFAULT_COUNT = 6
DEFAULT_SIZE = 384


def _render_cells(rng: np.random.Generator, size: int) -> np.ndarray:
    """Render one image: a dark field seeded with bright Gaussian blobs."""
    img = rng.normal(8.0, 3.0, size=(size, size)).clip(0, 255)  # faint noise floor
    n_cells = int(rng.integers(8, 26))
    yy, xx = np.mgrid[0:size, 0:size]

    for _ in range(n_cells):
        cy, cx = rng.integers(0, size, size=2)
        radius = float(rng.uniform(8, 20))
        peak = float(rng.uniform(120, 240))
        blob = peak * np.exp(-(((xx - cx) ** 2 + (yy - cy) ** 2) / (2 * radius**2)))
        img += blob

    return img.clip(0, 255).astype(np.uint8)


def generate_demo_images(
    folder: str | Path,
    count: int = DEFAULT_COUNT,
    size: int = DEFAULT_SIZE,
    seed: int = 42,
) -> list[Path]:
    """Write ``count`` synthetic cell images into ``folder``; return their paths."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    paths: list[Path] = []
    for i in range(count):
        arr = _render_cells(rng, size)
        # Green-channel fluorescence look: put signal in G, leave R/B dim.
        rgb = np.zeros((size, size, 3), dtype=np.uint8)
        rgb[..., 1] = arr
        dest = folder / f"demo_cells_{i + 1:02d}.png"
        Image.fromarray(rgb, mode="RGB").save(dest)
        paths.append(dest)
    return paths
