"""Pipeline CRUD routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models import User
from ..schemas import MessageOut, PipelineCreate, PipelineOut, PipelineUpdate
from ..services import pipeline_service
from ..utils.image_processing import MODULE_REGISTRY

router = APIRouter(prefix="/api/pipelines", tags=["pipelines"])


@router.get("/modules")
def modules() -> list[dict]:
    """Module library used by the frontend builder."""
    return MODULE_REGISTRY


@router.get("", response_model=list[PipelineOut])
def list_pipelines(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return pipeline_service.list_pipelines(db, user)


@router.post("", response_model=PipelineOut, status_code=status.HTTP_201_CREATED)
def create_pipeline(
    data: PipelineCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return pipeline_service.create_pipeline(db, user, data)


@router.get("/{pipeline_id}", response_model=PipelineOut)
def get_pipeline(
    pipeline_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return pipeline_service.get_owned_pipeline(db, user, pipeline_id)


@router.put("/{pipeline_id}", response_model=PipelineOut)
def update_pipeline(
    pipeline_id: str,
    data: PipelineUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return pipeline_service.update_pipeline(db, user, pipeline_id, data)


@router.delete("/{pipeline_id}", response_model=MessageOut)
def delete_pipeline(
    pipeline_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    pipeline_service.delete_pipeline(db, user, pipeline_id)
    return MessageOut(message="Pipeline deleted")


@router.post("/{pipeline_id}/clone", response_model=PipelineOut, status_code=201)
def clone_pipeline(
    pipeline_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return pipeline_service.clone_pipeline(db, user, pipeline_id)
