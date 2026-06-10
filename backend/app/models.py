"""SQLAlchemy ORM models."""
from __future__ import annotations

import datetime as dt

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import GUID, Base, JSONType, gen_uuid


def _utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    tier: Mapped[str] = mapped_column(String(16), default="free")  # free|pro|enterprise
    storage_used_gb: Mapped[float] = mapped_column(Float, default=0.0)
    settings: Mapped[dict] = mapped_column(JSONType, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )

    pipelines: Mapped[list["Pipeline"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    jobs: Mapped[list["BatchJob"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Pipeline(Base):
    __tablename__ = "pipelines"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    config: Mapped[dict] = mapped_column(JSONType, default=dict)  # {nodes, edges}
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime, default=_utcnow, onupdate=_utcnow
    )

    user: Mapped["User"] = relationship(back_populates="pipelines")
    jobs: Mapped[list["BatchJob"]] = relationship(back_populates="pipeline")


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    user_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    pipeline_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("pipelines.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(16), default="queued", index=True
    )  # queued|processing|completed|failed|cancelled
    input_folder_path: Mapped[str] = mapped_column(String(1024), default="")
    num_images: Mapped[int] = mapped_column(Integer, default=0)
    num_processed: Mapped[int] = mapped_column(Integer, default=0)
    num_failed: Mapped[int] = mapped_column(Integer, default=0)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0)
    result_folder_path: Mapped[str] = mapped_column(String(1024), default="")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    started_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    user: Mapped["User"] = relationship(back_populates="jobs")
    pipeline: Mapped["Pipeline"] = relationship(back_populates="jobs")
    results: Mapped[list["ProcessingResult"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class ProcessingResult(Base):
    __tablename__ = "processing_results"

    id: Mapped[str] = mapped_column(GUID, primary_key=True, default=gen_uuid)
    job_id: Mapped[str] = mapped_column(
        GUID, ForeignKey("batch_jobs.id", ondelete="CASCADE"), index=True
    )
    image_filename: Mapped[str] = mapped_column(String(512))
    metrics: Mapped[dict] = mapped_column(JSONType, default=dict)
    processed_image_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="success")  # success|failed
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[dt.datetime] = mapped_column(DateTime, default=_utcnow)

    job: Mapped["BatchJob"] = relationship(back_populates="results")
