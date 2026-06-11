"""Batch-job submission and lifecycle helpers."""
from __future__ import annotations

import datetime as dt

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from ..models import BatchJob, Pipeline, User
from ..services.image_service import list_images


def submit_job(
    db: Session, user: User, pipeline_id: str, input_folder_path: str
) -> BatchJob:
    pipeline = db.get(Pipeline, pipeline_id)
    if pipeline is None or pipeline.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Pipeline not found"
        )

    images = list_images(input_folder_path)
    if not images:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No supported images found in {input_folder_path}",
        )

    job = BatchJob(
        user_id=user.id,
        pipeline_id=pipeline_id,
        status="queued",
        input_folder_path=input_folder_path,
        num_images=len(images),
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Dispatch async. Imported here to avoid circular import at module load.
    from ..tasks.process_batch import process_batch

    process_batch.delay(job.id)
    # In eager mode (local/demo) the task has already run and committed by now,
    # so refresh to return the real status instead of the stale "queued".
    db.refresh(job)
    return job


def get_owned_job(db: Session, user: User, job_id: str) -> BatchJob:
    job = db.get(BatchJob, job_id)
    if job is None or job.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Job not found"
        )
    return job


def list_jobs(db: Session, user: User) -> list[BatchJob]:
    return (
        db.query(BatchJob)
        .filter(BatchJob.user_id == user.id)
        .order_by(BatchJob.created_at.desc())
        .all()
    )


def request_cancel(db: Session, user: User, job_id: str) -> BatchJob:
    job = get_owned_job(db, user, job_id)
    if job.status in ("completed", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Job already {job.status}",
        )
    job.cancel_requested = True
    if job.status == "queued":
        job.status = "cancelled"
        job.completed_at = dt.datetime.now(dt.timezone.utc)
    db.commit()
    db.refresh(job)
    return job
