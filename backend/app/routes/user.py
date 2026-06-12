"""User account / storage / settings routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..config import get_settings
from ..dependencies import get_current_user, get_db
from ..models import User
from ..schemas import StorageOut, TierLimitsOut, UserOut, UserSettingsUpdate

router = APIRouter(prefix="/api/user", tags=["user"])
settings = get_settings()


@router.get("/storage", response_model=StorageOut)
def storage(current_user: User = Depends(get_current_user)) -> StorageOut:
    limit = settings.tier_limits.get(current_user.tier, settings.free_tier_storage_gb)
    return StorageOut(
        storage_used_gb=current_user.storage_used_gb,
        storage_limit_gb=limit,
        tier=current_user.tier,
    )


@router.get("/tier-limits", response_model=TierLimitsOut)
def tier_limits(current_user: User = Depends(get_current_user)) -> TierLimitsOut:
    return TierLimitsOut(
        tier=current_user.tier,
        storage_limit_gb=settings.tier_limits.get(
            current_user.tier, settings.free_tier_storage_gb
        ),
        all_tiers=settings.tier_limits,
    )


@router.put("/settings", response_model=UserOut)
def update_settings(
    data: UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    current_user.settings = data.settings
    db.commit()
    db.refresh(current_user)
    return current_user
