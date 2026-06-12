"""Pipeline CRUD and validation."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models import Pipeline, User
from ..schemas import PipelineCreate, PipelineUpdate
from ..utils.validators import PipelineValidationError, validate_pipeline_config


def _validate(config: dict) -> None:
    try:
        validate_pipeline_config(config)
    except PipelineValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        )


def create_pipeline(db: Session, user: User, data: PipelineCreate) -> Pipeline:
    config = data.config.model_dump()
    _validate(config)
    pipeline = Pipeline(
        user_id=user.id,
        name=data.name,
        description=data.description,
        config=config,
        is_public=data.is_public,
    )
    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)
    return pipeline


def get_owned_pipeline(db: Session, user: User, pipeline_id: str) -> Pipeline:
    pipeline = db.get(Pipeline, pipeline_id)
    if pipeline is None or pipeline.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
        )
    return pipeline


def list_pipelines(db: Session, user: User) -> list[Pipeline]:
    return (
        db.query(Pipeline)
        .filter(Pipeline.user_id == user.id)
        .order_by(Pipeline.updated_at.desc())
        .all()
    )


def update_pipeline(
    db: Session, user: User, pipeline_id: str, data: PipelineUpdate
) -> Pipeline:
    pipeline = get_owned_pipeline(db, user, pipeline_id)
    if data.name is not None:
        pipeline.name = data.name
    if data.description is not None:
        pipeline.description = data.description
    if data.is_public is not None:
        pipeline.is_public = data.is_public
    if data.config is not None:
        config = data.config.model_dump()
        _validate(config)
        pipeline.config = config
        pipeline.version += 1
    db.commit()
    db.refresh(pipeline)
    return pipeline


def delete_pipeline(db: Session, user: User, pipeline_id: str) -> None:
    pipeline = get_owned_pipeline(db, user, pipeline_id)
    db.delete(pipeline)
    db.commit()


def clone_pipeline(db: Session, user: User, pipeline_id: str) -> Pipeline:
    source = get_owned_pipeline(db, user, pipeline_id)
    clone = Pipeline(
        user_id=user.id,
        name=f"{source.name} (copy)",
        description=source.description,
        config=source.config,
        is_public=False,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return clone
