"""Periodic cleanup of old job results (>30 days)."""
from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path

from ..celery_app import celery_app
from ..config import get_settings
from ..database import SessionLocal
from ..models import BatchJob

settings = get_settings()
RETENTION_DAYS = 30


@celery_app.task(name="cleanup_old_results")
def cleanup_old_results() -> dict:
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=RETENTION_DAYS)
    db = SessionLocal()
    removed = 0
    try:
        stale = (
            db.query(BatchJob)
            .filter(BatchJob.completed_at.isnot(None))
            .filter(BatchJob.completed_at < cutoff)
            .all()
        )
        for job in stale:
            folder = Path(job.result_folder_path or "")
            if folder.exists() and folder.is_dir():
                shutil.rmtree(folder, ignore_errors=True)
                removed += 1
        return {"removed_folders": removed}
    finally:
        db.close()
