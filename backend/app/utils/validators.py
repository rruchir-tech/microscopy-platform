"""Validation helpers for pipeline configs and image files."""
from __future__ import annotations

from .image_processing import VALID_MODULE_TYPES

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}


class PipelineValidationError(ValueError):
    pass


def validate_pipeline_config(config: dict) -> None:
    """Validate a pipeline's {nodes, edges} structure. Raises on problems."""
    if not isinstance(config, dict):
        raise PipelineValidationError("config must be an object")

    nodes = config.get("nodes", [])
    edges = config.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise PipelineValidationError("nodes and edges must be lists")

    node_ids = set()
    for node in nodes:
        nid = node.get("id")
        ntype = node.get("type")
        if not nid:
            raise PipelineValidationError("every node needs an id")
        if nid in node_ids:
            raise PipelineValidationError(f"duplicate node id: {nid}")
        node_ids.add(nid)
        if ntype not in VALID_MODULE_TYPES:
            raise PipelineValidationError(f"unknown module type: {ntype}")

    for edge in edges:
        src, tgt = edge.get("source"), edge.get("target")
        if src not in node_ids or tgt not in node_ids:
            raise PipelineValidationError(
                f"edge references unknown node(s): {src} -> {tgt}"
            )

    if nodes and _has_cycle(node_ids, edges):
        raise PipelineValidationError("pipeline graph must be acyclic")


def _has_cycle(node_ids: set[str], edges: list[dict]) -> bool:
    adj: dict[str, list[str]] = {n: [] for n in node_ids}
    for e in edges:
        adj[e["source"]].append(e["target"])
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in node_ids}

    def dfs(n: str) -> bool:
        color[n] = GRAY
        for m in adj[n]:
            if color[m] == GRAY:
                return True
            if color[m] == WHITE and dfs(m):
                return True
        color[n] = BLACK
        return False

    return any(color[n] == WHITE and dfs(n) for n in node_ids)


def is_image_file(filename: str) -> bool:
    return any(filename.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)
