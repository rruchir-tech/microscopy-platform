"""Celery task that runs a batch job: process every image, persist results,
write a CSV, and (optionally) a ZIP of annotated images."""
from __future__ import annotations

import csv
import datetime as dt
import logging
import zipfile
from pathlib import Path

from ..celery_app import celery_app
from ..config import get_settings
from ..database import SessionLocal
from ..models import BatchJob, Pipeline, ProcessingResult
from ..services.image_service import list_images, run_pipeline_on_image

logger = logging.getLogger("process_batch")
settings = get_settings()


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


@celery_app.task(bind=True, name="process_batch")
def process_batch(self, job_id: str) -> dict:
    db = SessionLocal()
    try:
        job = db.get(BatchJob, job_id)
        if job is None:
            return {"error": "job not found"}
        if job.cancel_requested:
            job.status = "cancelled"
            job.completed_at = _utcnow()
            db.commit()
            return {"status": "cancelled"}

        pipeline = db.get(Pipeline, job.pipeline_id)
        if pipeline is None:
            _fail(db, job, "pipeline no longer exists")
            return {"status": "failed"}

        result_dir = Path(settings.results_folder) / job.id
        result_dir.mkdir(parents=True, exist_ok=True)

        job.status = "processing"
        job.started_at = _utcnow()
        job.result_folder_path = str(result_dir)
        db.commit()

        images = list_images(job.input_folder_path)
        all_rows: list[dict] = []
        processed = 0
        failed = 0

        for idx, image_path in enumerate(images):
            db.refresh(job)
            if job.cancel_requested:
                job.status = "cancelled"
                job.completed_at = _utcnow()
                db.commit()
                return {"status": "cancelled", "processed": processed}

            try:
                out = run_pipeline_on_image(image_path, pipeline.config)
                rows = out["rows"] or [{}]
                for row in rows:
                    enriched = {"image_name": image_path.name, **out["aggregate"], **row}
                    all_rows.append(enriched)

                # Save the annotated overlay so users can see the segmentation.
                processed_image_path = None
                overlay = out.get("overlay")
                if overlay is not None:
                    img_path = result_dir / f"{image_path.stem}_annotated.png"
                    overlay.save(img_path)
                    processed_image_path = str(img_path)

                db.add(
                    ProcessingResult(
                        job_id=job.id,
                        image_filename=image_path.name,
                        metrics={"aggregate": out["aggregate"], "cells": out["rows"]},
                        processed_image_path=processed_image_path,
                        status="success",
                    )
                )
                processed += 1
            except Exception as exc:  # noqa: BLE001 - record per-image failure
                logger.exception("failed processing %s", image_path)
                db.add(
                    ProcessingResult(
                        job_id=job.id,
                        image_filename=image_path.name,
                        metrics={},
                        status="failed",
                        error=str(exc),
                    )
                )
                failed += 1

            job.num_processed = processed
            job.num_failed = failed
            job.progress_percent = int(((idx + 1) / max(len(images), 1)) * 100)
            db.commit()

        csv_path = result_dir / "results.csv"
        _write_csv(csv_path, all_rows)

        zip_path = result_dir / "results.zip"
        _write_zip(zip_path, csv_path)

        job.status = "completed"
        job.progress_percent = 100
        job.completed_at = _utcnow()
        db.commit()
        return {"status": "completed", "processed": processed, "failed": failed}
    except Exception as exc:  # noqa: BLE001
        logger.exception("batch job crashed")
        job = db.get(BatchJob, job_id)
        if job is not None:
            _fail(db, job, str(exc))
        return {"status": "failed", "error": str(exc)}
    finally:
        db.close()


def _fail(db, job: BatchJob, message: str) -> None:
    job.status = "failed"
    job.error_message = message
    job.completed_at = _utcnow()
    db.commit()


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("image_name\n", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _write_zip(zip_path: Path, csv_path: Path) -> None:
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        if csv_path.exists():
            zf.write(csv_path, csv_path.name)
        # Include any annotated images saved alongside the CSV.
        for img in csv_path.parent.glob("*.png"):
            zf.write(img, img.name)
