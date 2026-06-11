"""Batch-job routes."""
from __future__ import annotations

import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, PlainTextResponse
from sqlalchemy.orm import Session

from ..config import get_settings
from ..dependencies import get_current_user, get_db
from ..models import ProcessingResult, User
from ..schemas import ImageSourceOut, JobCreate, JobOut, ResultOut
from ..services import job_service
from ..services.demo_data import DEFAULT_COUNT, generate_demo_images
from ..utils.validators import is_image_file

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

_MAX_FILES = 200


def _user_input_dir(user: User, kind: str) -> Path:
    """A fresh per-user folder for one batch of input images."""
    folder = Path(get_settings().upload_folder) / str(user.id) / kind / uuid4().hex
    folder.mkdir(parents=True, exist_ok=True)
    return folder


@router.post(
    "/upload", response_model=ImageSourceOut, status_code=status.HTTP_201_CREATED
)
async def upload_images(
    files: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
):
    """Accept a batch of image files and stage them server-side for a job."""
    if len(files) > _MAX_FILES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files (max {_MAX_FILES})",
        )
    folder = _user_input_dir(user, "uploads")
    saved = 0
    for f in files:
        if not f.filename or not is_image_file(f.filename):
            continue
        # strip any path components to avoid traversal
        dest = folder / Path(f.filename).name
        with dest.open("wb") as out:
            shutil.copyfileobj(f.file, out)
        saved += 1
    if saved == 0:
        shutil.rmtree(folder, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No supported image files in upload (png/jpg/tif/bmp)",
        )
    return ImageSourceOut(input_folder_path=str(folder), num_images=saved)


@router.post(
    "/demo", response_model=ImageSourceOut, status_code=status.HTTP_201_CREATED
)
def create_demo_images(
    count: int = DEFAULT_COUNT,
    user: User = Depends(get_current_user),
):
    """Generate synthetic fluorescence-cell images to try a pipeline end-to-end."""
    count = max(1, min(count, 24))
    folder = _user_input_dir(user, "demo")
    paths = generate_demo_images(folder, count=count)
    return ImageSourceOut(input_folder_path=str(folder), num_images=len(paths))


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


@router.get("/{job_id}/results/{result_id}/image")
def get_result_image(
    job_id: str,
    result_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Serve the annotated overlay PNG for one processed image."""
    job = job_service.get_owned_job(db, user, job_id)
    result = db.get(ProcessingResult, result_id)
    if (
        result is None
        or result.job_id != job.id
        or not result.processed_image_path
    ):
        raise HTTPException(status_code=404, detail="No image for this result")
    path = Path(result.processed_image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file missing")
    return FileResponse(path, media_type="image/png")


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
