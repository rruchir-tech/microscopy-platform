"""Pre-built pipeline templates."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models import Pipeline, User
from ..schemas import PipelineOut, TemplateOut

router = APIRouter(prefix="/api/templates", tags=["templates"])


TEMPLATES: list[dict] = [
    {
        "id": "cell-counter",
        "name": "Cell Counter",
        "description": "Count cells and measure size in fluorescence images.",
        "config": {
            "nodes": [
                {"id": "n1", "type": "image_load", "params": {"target_size": 512}},
                {"id": "n2", "type": "preprocessing", "params": {"blur_kernel": 3, "normalize": True}},
                {"id": "n3", "type": "thresholding", "params": {"method": "otsu"}},
                {"id": "n4", "type": "cell_detection", "params": {"model_type": "cyto", "diameter": 15}},
                {"id": "n5", "type": "intensity_measurement", "params": {"channel": "gray"}},
                {"id": "n6", "type": "export_results", "params": {"include_images": True}},
            ],
            "edges": [
                {"source": "n1", "target": "n2"},
                {"source": "n2", "target": "n3"},
                {"source": "n3", "target": "n4"},
                {"source": "n4", "target": "n5"},
                {"source": "n5", "target": "n6"},
            ],
        },
    },
    {
        "id": "nuclei-intensity",
        "name": "Nuclei Intensity Profiler",
        "description": "Segment nuclei and quantify per-nucleus intensity.",
        "config": {
            "nodes": [
                {"id": "n1", "type": "image_load", "params": {"target_size": 1024}},
                {"id": "n2", "type": "preprocessing", "params": {"blur_kernel": 5, "normalize": True}},
                {"id": "n3", "type": "thresholding", "params": {"method": "adaptive"}},
                {"id": "n4", "type": "cell_detection", "params": {"model_type": "nuclei", "diameter": 10}},
                {"id": "n5", "type": "intensity_measurement", "params": {"channel": "blue"}},
                {"id": "n6", "type": "classification", "params": {"model_type": "heuristic"}},
                {"id": "n7", "type": "export_results", "params": {"include_images": True}},
            ],
            "edges": [
                {"source": "n1", "target": "n2"},
                {"source": "n2", "target": "n3"},
                {"source": "n3", "target": "n4"},
                {"source": "n4", "target": "n5"},
                {"source": "n5", "target": "n6"},
                {"source": "n6", "target": "n7"},
            ],
        },
    },
    {
        "id": "colocalization",
        "name": "Two-Channel Colocalization",
        "description": "Pearson + Manders colocalization for two-channel images.",
        "config": {
            "nodes": [
                {"id": "n1", "type": "image_load", "params": {"target_size": 512}},
                {"id": "n2", "type": "preprocessing", "params": {"normalize": True}},
                {"id": "n3", "type": "colocalization", "params": {"region_size": 32}},
                {"id": "n4", "type": "export_results", "params": {"include_images": False}},
            ],
            "edges": [
                {"source": "n1", "target": "n2"},
                {"source": "n2", "target": "n3"},
                {"source": "n3", "target": "n4"},
            ],
        },
    },
]

_BY_ID = {t["id"]: t for t in TEMPLATES}


@router.get("", response_model=list[TemplateOut])
def list_templates() -> list[dict]:
    return TEMPLATES


@router.post(
    "/{template_id}/instantiate",
    response_model=PipelineOut,
    status_code=status.HTTP_201_CREATED,
)
def instantiate_template(
    template_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    template = _BY_ID.get(template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    pipeline = Pipeline(
        user_id=user.id,
        name=template["name"],
        description=template["description"],
        config=template["config"],
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline
