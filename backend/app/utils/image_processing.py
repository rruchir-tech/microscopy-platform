"""Image-processing modules and the pipeline executor.

Each module is a pure function ``fn(ctx, params) -> ctx`` that reads and writes
keys on a shared per-image context dict. Modules are chained by the executor
following the pipeline's edge list.

Heavy dependencies (OpenCV, scikit-image, scikit-learn, CellPose) are imported
lazily. When unavailable, pure-NumPy fallbacks keep the pipeline functional so
the platform works in minimal environments and tests run without ML downloads.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Callable

import numpy as np

logger = logging.getLogger("image_processing")

Context = dict[str, Any]
ModuleFn = Callable[[Context, dict], Context]


# --------------------------------------------------------------------------- #
# Optional dependency helpers
# --------------------------------------------------------------------------- #
def _try_import(name: str):
    try:
        return __import__(name)
    except Exception:  # pragma: no cover - depends on environment
        return None


def _load_cv2():
    try:
        import cv2  # type: ignore

        return cv2
    except Exception:  # pragma: no cover
        return None


# --------------------------------------------------------------------------- #
# Pure-NumPy primitives (fallbacks)
# --------------------------------------------------------------------------- #
def to_gray(img: np.ndarray) -> np.ndarray:
    if img.ndim == 2:
        return img.astype(np.float64)
    # Luminosity weights for RGB
    rgb = img[..., :3].astype(np.float64)
    return rgb @ np.array([0.299, 0.587, 0.114])


def gaussian_blur(img: np.ndarray, kernel: int) -> np.ndarray:
    """Separable Gaussian blur. Uses cv2 when available, else NumPy convolution."""
    if kernel <= 1:
        return img
    if kernel % 2 == 0:
        kernel += 1
    cv2 = _load_cv2()
    if cv2 is not None:
        return cv2.GaussianBlur(img, (kernel, kernel), 0)

    sigma = max(kernel / 6.0, 0.5)
    ax = np.arange(kernel) - kernel // 2
    k1d = np.exp(-(ax**2) / (2 * sigma**2))
    k1d /= k1d.sum()

    def conv1d(a: np.ndarray, axis: int) -> np.ndarray:
        pad = kernel // 2
        a = np.apply_along_axis(
            lambda m: np.convolve(np.pad(m, pad, mode="edge"), k1d, mode="valid"),
            axis,
            a,
        )
        return a

    work = img.astype(np.float64)
    if work.ndim == 2:
        work = conv1d(conv1d(work, 0), 1)
    else:
        for c in range(work.shape[2]):
            work[..., c] = conv1d(conv1d(work[..., c], 0), 1)
    return work


def otsu_threshold(gray: np.ndarray) -> float:
    """Otsu threshold over the image's actual value range (pure NumPy).

    Histograms across [min, max] with 256 bins, so it works correctly for 8-bit,
    16-bit, and float images — matching ImageJ's default auto-threshold rather
    than assuming a 0-255 range.
    """
    g = np.asarray(gray, dtype=np.float64).ravel()
    mn = float(g.min())
    mx = float(g.max())
    if mx <= mn:
        return mn

    nbins = 256
    hist, edges = np.histogram(g, bins=nbins, range=(mn, mx))
    centers = (edges[:-1] + edges[1:]) / 2.0
    total = g.size
    sum_total = float(np.dot(centers, hist))
    sum_b = 0.0
    w_b = 0.0
    max_var = 0.0
    threshold = mn
    for t in range(nbins):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += centers[t] * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_total - sum_b) / w_f
        between = w_b * w_f * (m_b - m_f) ** 2
        if between > max_var:
            max_var = between
            threshold = centers[t]
    return float(threshold)


def connected_components(mask: np.ndarray) -> np.ndarray:
    """Label connected components (4-connectivity). Uses scipy/skimage when
    available, else an iterative flood-fill fallback."""
    ndi = _try_import("scipy.ndimage")
    if ndi is not None:  # pragma: no cover - env dependent
        import scipy.ndimage as sndi  # type: ignore

        labels, _ = sndi.label(mask)
        return labels.astype(np.int32)

    ski = _try_import("skimage.measure")
    if ski is not None:  # pragma: no cover - env dependent
        from skimage.measure import label as sklabel  # type: ignore

        return sklabel(mask, connectivity=1).astype(np.int32)

    # Pure-python BFS flood fill fallback
    labels = np.zeros(mask.shape, dtype=np.int32)
    current = 0
    h, w = mask.shape
    for i in range(h):
        for j in range(w):
            if mask[i, j] and labels[i, j] == 0:
                current += 1
                stack = [(i, j)]
                labels[i, j] = current
                while stack:
                    y, x = stack.pop()
                    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        ny, nx = y + dy, x + dx
                        if (
                            0 <= ny < h
                            and 0 <= nx < w
                            and mask[ny, nx]
                            and labels[ny, nx] == 0
                        ):
                            labels[ny, nx] = current
                            stack.append((ny, nx))
    return labels


# --------------------------------------------------------------------------- #
# Module implementations
# --------------------------------------------------------------------------- #
def m_image_load(ctx: Context, params: dict) -> Context:
    """Resize the already-loaded image to ``target_size`` (longest side)."""
    img = ctx["image"]
    target = params.get("target_size")
    if target:
        cv2 = _load_cv2()
        h, w = img.shape[:2]
        scale = target / max(h, w)
        if scale != 1.0:
            new_w, new_h = max(1, int(w * scale)), max(1, int(h * scale))
            if cv2 is not None:
                img = cv2.resize(img, (new_w, new_h))
            else:
                ys = (np.linspace(0, h - 1, new_h)).astype(int)
                xs = (np.linspace(0, w - 1, new_w)).astype(int)
                img = img[np.ix_(ys, xs)] if img.ndim == 2 else img[np.ix_(ys, xs, range(img.shape[2]))]
    ctx["image"] = img
    ctx["original"] = img.copy()
    return ctx


def m_preprocessing(ctx: Context, params: dict) -> Context:
    img = ctx["image"].astype(np.float64)
    kernel = int(params.get("blur_kernel", 0) or 0)
    if kernel and kernel > 1:
        img = gaussian_blur(img, kernel)

    denoise = float(params.get("denoise_strength", 0) or 0)
    if denoise > 0:
        ski = _try_import("skimage.restoration")
        if ski is not None:  # pragma: no cover - env dependent
            from skimage.restoration import denoise_tv_chambolle  # type: ignore

            img = denoise_tv_chambolle(img, weight=denoise * 0.2) * (
                img.max() if img.max() > 0 else 1
            )
        else:
            # crude denoise: light blur proportional to strength
            img = gaussian_blur(img, 3)

    if params.get("normalize"):
        mn, mx = float(img.min()), float(img.max())
        if mx > mn:
            img = (img - mn) / (mx - mn) * 255.0
    ctx["image"] = img
    return ctx


def m_thresholding(ctx: Context, params: dict) -> Context:
    gray = to_gray(ctx["image"])
    method = params.get("method", "otsu")
    if method == "manual":
        thr = float(params.get("threshold_value", 127))
        mask = gray > thr
    elif method == "adaptive":
        # local mean threshold via blurred reference
        ref = gaussian_blur(gray, int(params.get("block_size", 15)))
        mask = gray > (ref - float(params.get("offset", 2)))
    else:  # otsu
        thr = otsu_threshold(gray)
        mask = gray > thr
    ctx["mask"] = mask.astype(bool)
    return ctx


def m_cell_detection(ctx: Context, params: dict) -> Context:
    """Label individual cells. Uses CellPose when installed, else falls back to
    connected-components on the threshold mask (or on an Otsu mask)."""
    model_type = params.get("model_type", "cyto")
    diameter = params.get("diameter")

    cellpose = _try_import("cellpose")
    if cellpose is not None:  # pragma: no cover - requires torch + model download
        try:
            from cellpose import models as cp_models  # type: ignore

            model = cp_models.Cellpose(model_type=model_type)
            gray = to_gray(ctx["image"])
            masks, _, _, _ = model.eval(
                gray, diameter=diameter, channels=[0, 0]
            )
            ctx["labels"] = masks.astype(np.int32)
            return ctx
        except Exception as exc:  # fall through to classical method
            logger.warning("CellPose failed (%s); using fallback segmentation", exc)

    mask = ctx.get("mask")
    if mask is None:
        gray = to_gray(ctx["image"])
        mask = gray > otsu_threshold(gray)
    labels = connected_components(mask.astype(bool))
    # ImageJ "Analyze Particles": drop objects below a minimum area to remove
    # single-pixel noise. Default scales with the requested diameter if given.
    min_size = params.get("min_size")
    if min_size is None:
        min_size = max(10, int(np.pi * (float(diameter) / 2) ** 2 * 0.1)) if diameter else 10
    ctx["labels"] = filter_by_size(labels, int(min_size))
    return ctx


def filter_by_size(labels: np.ndarray, min_size: int) -> np.ndarray:
    """Zero out components smaller than ``min_size`` px and renumber the rest
    contiguously (1..N), so the cell count reflects real objects."""
    if min_size <= 1:
        return labels
    out = np.zeros_like(labels)
    next_id = 0
    for cid in (i for i in np.unique(labels) if i != 0):
        sel = labels == cid
        if int(sel.sum()) >= min_size:
            next_id += 1
            out[sel] = next_id
    return out


def _region_stats(labels: np.ndarray, intensity: np.ndarray) -> list[dict]:
    cells = []
    ids = [i for i in np.unique(labels) if i != 0]
    for cid in ids:
        sel = labels == cid
        vals = intensity[sel]
        if vals.size == 0:
            continue
        ys, xs = np.where(sel)
        area = int(vals.size)
        # circularity proxy from bbox
        bbox_h = ys.max() - ys.min() + 1
        bbox_w = xs.max() - xs.min() + 1
        circularity = float(area / (np.pi * (max(bbox_h, bbox_w) / 2) ** 2 + 1e-9))
        cells.append(
            {
                "cell_id": int(cid),
                "area": area,
                "mean_intensity": float(vals.mean()),
                "max_intensity": float(vals.max()),
                "sum_intensity": float(vals.sum()),
                "centroid_x": float(xs.mean()),
                "centroid_y": float(ys.mean()),
                "circularity": round(min(circularity, 1.0), 4),
            }
        )
    return cells


def m_intensity_measurement(ctx: Context, params: dict) -> Context:
    labels = ctx.get("labels")
    if labels is None:
        raise ValueError("intensity_measurement requires a prior cell_detection step")

    original = ctx.get("original", ctx["image"])
    channel = params.get("channel", "gray")
    if original.ndim == 3 and channel in ("red", "green", "blue", "r", "g", "b"):
        idx = {"red": 0, "r": 0, "green": 1, "g": 1, "blue": 2, "b": 2}[channel]
        intensity = original[..., idx].astype(np.float64)
    else:
        intensity = to_gray(original)

    ctx["cells"] = _region_stats(labels, intensity)
    return ctx


def m_colocalization(ctx: Context, params: dict) -> Context:
    original = ctx.get("original", ctx["image"])
    if original.ndim != 3 or original.shape[2] < 2:
        ctx.setdefault("aggregate", {})["colocalization"] = None
        return ctx
    ch1 = original[..., 0].astype(np.float64).ravel()
    ch2 = original[..., 1].astype(np.float64).ravel()

    # Pearson correlation
    if ch1.std() > 0 and ch2.std() > 0:
        pearson = float(np.corrcoef(ch1, ch2)[0, 1])
    else:
        pearson = 0.0

    # Manders coefficients
    m1 = float(ch1[ch2 > 0].sum() / (ch1.sum() + 1e-9))
    m2 = float(ch2[ch1 > 0].sum() / (ch2.sum() + 1e-9))

    ctx.setdefault("aggregate", {})["colocalization"] = {
        "pearson": round(pearson, 4),
        "manders_m1": round(m1, 4),
        "manders_m2": round(m2, 4),
    }
    return ctx


def m_classification(ctx: Context, params: dict) -> Context:
    """Classify each detected cell. Loads a scikit-learn model when present;
    otherwise applies a transparent heuristic on area + intensity."""
    cells = ctx.get("cells", [])
    if not cells:
        return ctx

    threshold = float(params.get("confidence_threshold", 0.5))
    model_path = params.get("model_path")
    features = np.array(
        [[c["area"], c["mean_intensity"], c["circularity"]] for c in cells]
    )

    model = None
    if model_path and Path(model_path).exists():
        joblib = _try_import("joblib")
        if joblib is not None:  # pragma: no cover - env dependent
            import joblib as jl  # type: ignore

            model = jl.load(model_path)

    if model is not None:  # pragma: no cover - requires a trained model
        preds = model.predict(features)
        probs = (
            model.predict_proba(features).max(axis=1)
            if hasattr(model, "predict_proba")
            else np.ones(len(cells))
        )
        for c, p, pr in zip(cells, preds, probs):
            c["class"] = str(p) if pr >= threshold else "uncertain"
            c["confidence"] = round(float(pr), 4)
    else:
        # Heuristic: large + bright => "abnormal", tiny => "debris", else "normal"
        areas = features[:, 0]
        med_area = float(np.median(areas)) if len(areas) else 0.0
        for c in cells:
            if c["area"] < 0.3 * med_area:
                label = "debris"
            elif c["area"] > 1.8 * med_area and c["mean_intensity"] > np.median(
                features[:, 1]
            ):
                label = "abnormal"
            else:
                label = "normal"
            c["class"] = label
            c["confidence"] = 0.66
    return ctx


def m_export_results(ctx: Context, params: dict) -> Context:
    ctx["include_images"] = bool(params.get("include_images", False))
    ctx["exported"] = True
    return ctx


MODULE_FUNCS: dict[str, ModuleFn] = {
    "image_load": m_image_load,
    "preprocessing": m_preprocessing,
    "thresholding": m_thresholding,
    "cell_detection": m_cell_detection,
    "intensity_measurement": m_intensity_measurement,
    "colocalization": m_colocalization,
    "classification": m_classification,
    "export_results": m_export_results,
}


# --------------------------------------------------------------------------- #
# Module registry (drives the frontend module library + validation)
# --------------------------------------------------------------------------- #
MODULE_REGISTRY: list[dict] = [
    {
        "type": "image_load",
        "label": "Image Load",
        "category": "input",
        "params": [
            {"name": "target_size", "type": "number", "default": 512, "min": 64, "max": 4096},
        ],
    },
    {
        "type": "preprocessing",
        "label": "Preprocessing",
        "category": "transform",
        "params": [
            {"name": "blur_kernel", "type": "select", "options": [0, 3, 5, 7, 9], "default": 3},
            {"name": "normalize", "type": "boolean", "default": True},
            {"name": "denoise_strength", "type": "slider", "min": 0, "max": 1, "step": 0.1, "default": 0},
        ],
    },
    {
        "type": "thresholding",
        "label": "Thresholding",
        "category": "transform",
        "params": [
            {"name": "method", "type": "select", "options": ["otsu", "manual", "adaptive"], "default": "otsu"},
            {"name": "threshold_value", "type": "slider", "min": 0, "max": 255, "step": 1, "default": 127},
        ],
    },
    {
        "type": "cell_detection",
        "label": "Cell Detection",
        "category": "analysis",
        "params": [
            {"name": "model_type", "type": "select", "options": ["cyto", "nuclei", "custom"], "default": "cyto"},
            {"name": "diameter", "type": "number", "default": 15, "min": 1, "max": 200},
        ],
    },
    {
        "type": "intensity_measurement",
        "label": "Intensity Measurement",
        "category": "analysis",
        "params": [
            {"name": "channel", "type": "select", "options": ["gray", "red", "green", "blue"], "default": "gray"},
        ],
    },
    {
        "type": "colocalization",
        "label": "Colocalization",
        "category": "analysis",
        "params": [
            {"name": "region_size", "type": "number", "default": 32, "min": 4, "max": 256},
        ],
    },
    {
        "type": "classification",
        "label": "Classification",
        "category": "analysis",
        "params": [
            {"name": "model_type", "type": "select", "options": ["heuristic", "random_forest", "custom"], "default": "heuristic"},
            {"name": "confidence_threshold", "type": "slider", "min": 0, "max": 1, "step": 0.05, "default": 0.5},
        ],
    },
    {
        "type": "export_results",
        "label": "Export Results",
        "category": "output",
        "params": [
            {"name": "include_images", "type": "boolean", "default": True},
        ],
    },
]

VALID_MODULE_TYPES = set(MODULE_FUNCS.keys())
