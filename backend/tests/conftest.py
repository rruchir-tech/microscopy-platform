"""Pytest fixtures: isolated SQLite DB + authenticated test client."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

# Configure env BEFORE importing the app so settings pick it up.
_tmp = tempfile.mkdtemp(prefix="microscopy-test-")
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["JWT_SECRET"] = "test-secret"
os.environ["CELERY_TASK_ALWAYS_EAGER"] = "true"
os.environ["UPLOAD_FOLDER"] = f"{_tmp}/uploads"
os.environ["RESULTS_FOLDER"] = f"{_tmp}/results"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_client(client):
    """A client with Authorization header set for a freshly registered user."""
    import uuid

    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    username = f"user{uuid.uuid4().hex[:8]}"
    resp = client.post(
        "/api/auth/register",
        json={"email": email, "username": username, "password": "supersecret123"},
    )
    assert resp.status_code == 201, resp.text
    token = resp.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture
def sample_images(tmp_path) -> Path:
    """Create a folder with a few small synthetic images containing bright blobs."""
    import numpy as np
    from PIL import Image

    folder = tmp_path / "images"
    folder.mkdir()
    rng = np.random.default_rng(42)
    for i in range(3):
        arr = np.zeros((64, 64, 3), dtype=np.uint8)
        # draw a few bright square "cells"
        for _ in range(5):
            y, x = rng.integers(5, 55, size=2)
            arr[y : y + 4, x : x + 4] = 220
        Image.fromarray(arr).save(folder / f"img_{i}.png")
    return folder
