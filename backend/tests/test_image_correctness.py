"""Quantitative correctness checks: the pipeline must recover a known cell
count and measure *raw* 16-bit intensities (not 8-bit-clipped values), so the
numbers are comparable to what ImageJ would report.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from app.services.analysis import build_config
from app.services.image_service import load_image, run_pipeline_on_image
from app.utils.image_processing import otsu_threshold

DISK_VALUE = 5000  # well outside 8-bit range -> proves no downcast
BG_VALUE = 0
RADIUS = 16
CENTERS = [(50, 50), (50, 128), (50, 206), (190, 80), (190, 190)]  # 5, separated


def _make_16bit_image(path) -> np.ndarray:
    size = 256
    img = np.full((size, size), BG_VALUE, dtype=np.uint16)
    yy, xx = np.mgrid[0:size, 0:size]
    for cy, cx in CENTERS:
        img[(yy - cy) ** 2 + (xx - cx) ** 2 <= RADIUS**2] = DISK_VALUE
    Image.fromarray(img).save(path)  # 16-bit grayscale TIFF (mode I;16)
    return img


def test_load_preserves_16bit(tmp_path):
    p = tmp_path / "cells16.tif"
    _make_16bit_image(p)
    arr = load_image(p)
    assert arr.dtype == np.uint16
    assert int(arr.max()) == DISK_VALUE  # not clipped to 255


def test_otsu_handles_16bit_range():
    g = np.full((64, 64), BG_VALUE, dtype=np.uint16)
    g[:32] = DISK_VALUE
    thr = otsu_threshold(g.astype(np.float64))
    assert BG_VALUE < thr < DISK_VALUE  # a sane split, not a mod-256 artifact


def test_pipeline_recovers_count_and_raw_intensity(tmp_path):
    p = tmp_path / "cells16.tif"
    _make_16bit_image(p)
    out = run_pipeline_on_image(p, build_config({"cell_count", "intensity"}))

    assert out["aggregate"]["cell_count"] == len(CENTERS)

    cells = out["rows"]
    assert len(cells) == len(CENTERS)
    for c in cells:
        # max sits at the disk core: exactly the raw 16-bit value
        assert 4900 <= c["max_intensity"] <= DISK_VALUE
        # mean is far above the 8-bit ceiling -> raw values were measured
        assert c["mean_intensity"] > 1000
