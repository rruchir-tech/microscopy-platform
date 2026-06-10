"""Batch-job routes."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models import ProcessingResult, User
from ..schemas import JobCreate, JobOut, MessageOut, ResultOut
from ..services import job_service

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(
    data: JobCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return job_service.submit_job(db, user, data.pipeline_id, data.input_folder_path)


@router.get("", response_model=list[JobOut])
def list_jobs(
    db: Session = Depends(get_db), user: User = Depends(get_current_user)
):
    return job_service.list_jobs(db, user)


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return job_service.get_owned_job(db, user, job_id)


@router.get("/{job_id}/results", response_model=list[ResultOut])
def get_results(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job_service.get_owned_job(db, user, job_id)  # ownership check
    return (
        db.query(ProcessingResult)
        .filter(ProcessingResult.job_id == job_id)
        .order_by(ProcessingResult.processed_at.asc())
        .all()
    )


@router.get("/{job_id}/results.csv", response_class=PlainTextResponse)
def get_results_csv(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = job_service.get_owned_job(db, user, job_id)
    csv_path = Path(job.result_folder_path or "") / "results.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="Results CSV not ready")
    return PlainTextResponse(csv_path.read_text(encoding="utf-8"))


@router.get("/{job_id}/download")
def download_zip(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    job = job_service.get_owned_job(db, user, job_id)
    zip_path = Path(job.result_folder_path or "") / "results.zip"
    if not zip_path.exists():
        raise HTTPException(status_code=404, detail="Results archive not ready")
    return FileResponse(
        zip_path, media_type="application/zip", filename=f"job-{job_id}-results.zip"
    )


@router.post("/{job_id}/cancel", response_model=JobOut)
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return job_service.request_cancel(db, user, job_id)
