"""Quantitative correctness checks: the pipeline must recover a known cell
count and measure *raw* 16-bit intensities (not 8-bit-clipped values), so the
numbers are comparable to what ImageJ would report.
"""
from __future__ import annotations

import numpy as np
from PIL import Image

from app.services.analysis import build_config
from app.services.image_service import load_image, run_pipeline_on_image
from app.utils.image_processing import (
    _region_stats,
    find_maxima,
    isodata_threshold,
    mean_threshold,
    otsu_threshold,
    triangle_threshold,
)

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


def _disk_labels(size=128, r=30):
    img = np.zeros((size, size), dtype=np.uint16)
    yy, xx = np.mgrid[0:size, 0:size]
    disk = (yy - size // 2) ** 2 + (xx - size // 2) ** 2 <= r**2
    img[disk] = 3000
    labels = disk.astype(np.int32)
    return labels, img, r


def test_shape_descriptors_for_a_disk():
    """A filled disk should score near-perfect circularity/roundness, AR ~1,
    and a Feret diameter close to 2r — ImageJ-comparable shape descriptors."""
    labels, img, r = _disk_labels()
    stats = _region_stats(labels, img.astype(np.float64))[0]
    assert stats["circularity"] > 0.85
    assert stats["roundness"] > 0.85
    assert stats["aspect_ratio"] < 1.2
    assert abs(stats["feret_max"] - 2 * r) < 4
    # full Measure set present
    for k in ("perimeter", "median_intensity", "std_intensity", "min_intensity"):
        assert k in stats


def test_confluence_percent_area(tmp_path):
    """The pipeline reports % area coverage (ImageJ Area Fraction)."""
    p = tmp_path / "cells16.tif"
    img = _make_16bit_image(p)
    out = run_pipeline_on_image(p, build_config({"cell_count", "intensity"}))
    pct = out["aggregate"]["percent_area"]
    expected = 100.0 * (img > 0).sum() / img.size  # known foreground fraction
    assert 0 < pct < 100
    assert abs(pct - expected) < 3.0  # within a few % of the true coverage


def test_auto_threshold_methods_split_two_levels():
    g = np.full((64, 64), 100.0)
    g[:32] = 4000.0
    for fn in (otsu_threshold, isodata_threshold, triangle_threshold):
        thr = fn(g)
        assert 100 < thr < 4000, f"{fn.__name__} -> {thr}"
    assert abs(mean_threshold(g) - g.mean()) < 1e-6


def test_find_maxima_counts_puncta():
    size = 120
    img = np.zeros((size, size), dtype=np.float64)
    spots = [(20, 20), (20, 90), (90, 20), (90, 90), (55, 55)]
    yy, xx = np.mgrid[0:size, 0:size]
    for cy, cx in spots:
        img += 2000 * np.exp(-(((yy - cy) ** 2 + (xx - cx) ** 2) / (2 * 4**2)))
    coords = find_maxima(img, min_distance=5, noise_k=2.0)
    assert len(coords) == len(spots)
