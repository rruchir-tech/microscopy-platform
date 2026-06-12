"""User registration and authentication logic."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..models import User
from ..schemas import UserRegister
from ..utils.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)


def register_user(db: Session, data: UserRegister) -> User:
    existing = (
        db.query(User)
        .filter(or_(User.email == data.email, User.username == data.username))
        .first()
    )
    if existing:
        field = "email" if existing.email == data.email else "username"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A user with this {field} already exists",
        )

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        tier="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def seed_demo_user(db: Session) -> None:
    """Ensure a ready-to-use demo account exists (demo@demo.com / demo12345)."""
    if db.query(User).filter(User.email == "demo@demo.com").first():
        return
    db.add(
        User(
            email="demo@demo.com",
            username="demo",
            password_hash=hash_password("demo12345"),
            tier="free",
        )
    )
    db.commit()


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    return user


def issue_tokens(user: User) -> dict[str, str]:
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }
