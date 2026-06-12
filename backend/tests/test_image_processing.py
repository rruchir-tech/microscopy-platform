import numpy as np

from app.services.image_service import run_pipeline_on_image, topo_order
from app.utils.image_processing import (
    connected_components,
    otsu_threshold,
    to_gray,
)
from app.utils.validators import (
    PipelineValidationError,
    validate_pipeline_config,
)


def test_otsu_separates_bimodal():
    img = np.zeros((20, 20))
    img[:, 10:] = 200
    thr = otsu_threshold(img)
    # Threshold must separate the two populations: dark (0) below, bright (200) above.
    assert 0 <= thr < 200
    assert (img > thr).sum() == 200  # only the bright half is selected


def test_connected_components_counts_blobs():
    mask = np.zeros((10, 10), dtype=bool)
    mask[1:3, 1:3] = True
    mask[6:8, 6:8] = True
    labels = connected_components(mask)
    assert labels.max() == 2


def test_to_gray_shapes():
    rgb = np.zeros((5, 5, 3))
    assert to_gray(rgb).shape == (5, 5)
    gray = np.zeros((5, 5))
    assert to_gray(gray).shape == (5, 5)


def test_topo_order_linear():
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    edges = [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}]
    ordered = [n["id"] for n in topo_order(nodes, edges)]
    assert ordered == ["a", "b", "c"]


def test_run_pipeline_on_image_produces_cells(tmp_path):
    from PIL import Image

    arr = np.zeros((40, 40, 3), dtype=np.uint8)
    arr[5:9, 5:9] = 230
    arr[20:24, 20:24] = 230
    path = tmp_path / "cells.png"
    Image.fromarray(arr).save(path)

    config = {
        "nodes": [
            {"id": "n1", "type": "image_load", "params": {"target_size": 40}},
            {"id": "n2", "type": "thresholding", "params": {"method": "otsu"}},
            {"id": "n3", "type": "cell_detection", "params": {}},
            {"id": "n4", "type": "intensity_measurement", "params": {"channel": "gray"}},
            {"id": "n5", "type": "export_results", "params": {}},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n3"},
            {"source": "n3", "target": "n4"},
            {"source": "n4", "target": "n5"},
        ],
    }
    out = run_pipeline_on_image(path, config)
    assert out["aggregate"]["cell_count"] >= 2
    assert all("mean_intensity" in row for row in out["rows"])


def test_validate_pipeline_config_ok():
    validate_pipeline_config(
        {"nodes": [{"id": "n1", "type": "image_load"}], "edges": []}
    )


def test_validate_pipeline_config_unknown_type():
    try:
        validate_pipeline_config(
            {"nodes": [{"id": "n1", "type": "nope"}], "edges": []}
        )
        assert False, "expected error"
    except PipelineValidationError:
        pass
