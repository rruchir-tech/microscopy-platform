"""Pydantic request/response schemas."""
from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ----- Auth -----
class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: EmailStr
    username: str
    tier: str
    storage_used_gb: float
    created_at: dt.datetime


class UserSettingsUpdate(BaseModel):
    settings: dict[str, Any]


# ----- Pipeline -----
class PipelineNode(BaseModel):
    id: str
    type: str
    params: dict[str, Any] = Field(default_factory=dict)
    # Optional UI position, ignored by the executor.
    position: dict[str, float] | None = None


class PipelineEdge(BaseModel):
    source: str
    target: str


class PipelineConfig(BaseModel):
    nodes: list[PipelineNode] = Field(default_factory=list)
    edges: list[PipelineEdge] = Field(default_factory=list)


class PipelineCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = ""
    config: PipelineConfig = Field(default_factory=PipelineConfig)
    is_public: bool = False


class PipelineUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    description: str | None = None
    config: PipelineConfig | None = None
    is_public: bool | None = None


class PipelineOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    name: str
    description: str
    config: dict[str, Any]
    version: int
    is_public: bool
    created_at: dt.datetime
    updated_at: dt.datetime


# ----- Jobs -----
class JobCreate(BaseModel):
    pipeline_id: str
    input_folder_path: str = Field(
        ..., description="Server-side folder of images to process"
    )


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    pipeline_id: str | None
    status: str
    input_folder_path: str
    num_images: int
    num_processed: int
    num_failed: int
    progress_percent: int
    result_folder_path: str
    error_message: str | None
    started_at: dt.datetime | None
    completed_at: dt.datetime | None
    created_at: dt.datetime


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    image_filename: str
    metrics: dict[str, Any]
    status: str
    error: str | None
    processed_at: dt.datetime


# ----- Templates -----
class TemplateOut(BaseModel):
    id: str
    name: str
    description: str
    config: PipelineConfig


# ----- Misc -----
class StorageOut(BaseModel):
    storage_used_gb: float
    storage_limit_gb: float
    tier: str


class TierLimitsOut(BaseModel):
    tier: str
    storage_limit_gb: float
    all_tiers: dict[str, float]


class MessageOut(BaseModel):
    message: str
