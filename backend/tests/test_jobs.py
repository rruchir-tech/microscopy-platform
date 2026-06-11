"""End-to-end job test. Celery runs eagerly (CELERY_TASK_ALWAYS_EAGER=true)."""

PIPELINE = {
    "nodes": [
        {"id": "n1", "type": "image_load", "params": {"target_size": 64}},
        {"id": "n2", "type": "thresholding", "params": {"method": "otsu"}},
        {"id": "n3", "type": "cell_detection", "params": {}},
        {"id": "n4", "type": "intensity_measurement", "params": {"channel": "gray"}},
        {"id": "n5", "type": "export_results", "params": {"include_images": False}},
    ],
    "edges": [
        {"source": "n1", "target": "n2"},
        {"source": "n2", "target": "n3"},
        {"source": "n3", "target": "n4"},
        {"source": "n4", "target": "n5"},
    ],
}


def _make_pipeline(auth_client):
    r = auth_client.post(
        "/api/pipelines", json={"name": "Job Pipeline", "config": PIPELINE}
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_submit_job_processes_images(auth_client, sample_images):
    pid = _make_pipeline(auth_client)
    r = auth_client.post(
        "/api/jobs",
        json={"pipeline_id": pid, "input_folder_path": str(sample_images)},
    )
    assert r.status_code == 201, r.text
    job = r.json()
    assert job["num_images"] == 3

    # With eager Celery the job finishes synchronously during submit.
    detail = auth_client.get(f"/api/jobs/{job['id']}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "completed"
    assert detail.json()["progress_percent"] == 100

    results = auth_client.get(f"/api/jobs/{job['id']}/results")
    assert results.status_code == 200
    assert len(results.json()) == 3

    csv = auth_client.get(f"/api/jobs/{job['id']}/results.csv")
    assert csv.status_code == 200
    assert "image_name" in csv.text


def test_job_empty_folder_rejected(auth_client, tmp_path):
    pid = _make_pipeline(auth_client)
    empty = tmp_path / "empty"
    empty.mkdir()
    r = auth_client.post(
        "/api/jobs", json={"pipeline_id": pid, "input_folder_path": str(empty)}
    )
    assert r.status_code == 400


def test_job_not_found(auth_client):
    assert auth_client.get("/api/jobs/00000000-0000-0000-0000-000000000000").status_code == 404


def test_demo_images_then_job(auth_client):
    """Demo generator stages images that a real job can process end-to-end."""
    src = auth_client.post("/api/jobs/demo?count=4")
    assert src.status_code == 201, src.text
    assert src.json()["num_images"] == 4
    folder = src.json()["input_folder_path"]

    pid = _make_pipeline(auth_client)
    r = auth_client.post(
        "/api/jobs", json={"pipeline_id": pid, "input_folder_path": folder}
    )
    assert r.status_code == 201, r.text
    job = r.json()
    assert job["num_images"] == 4

    detail = auth_client.get(f"/api/jobs/{job['id']}")
    assert detail.json()["status"] == "completed"
    assert detail.json()["num_processed"] == 4


def test_annotated_image_served(auth_client):
    """A processed image exposes has_image and serves an annotated PNG."""
    folder = auth_client.post("/api/jobs/demo?count=2").json()["input_folder_path"]
    pid = _make_pipeline(auth_client)
    job = auth_client.post(
        "/api/jobs", json={"pipeline_id": pid, "input_folder_path": folder}
    ).json()

    results = auth_client.get(f"/api/jobs/{job['id']}/results").json()
    assert results and all(r["has_image"] for r in results)

    rid = results[0]["id"]
    img = auth_client.get(f"/api/jobs/{job['id']}/results/{rid}/image")
    assert img.status_code == 200
    assert img.headers["content-type"] == "image/png"
    assert img.content[:8] == b"\x89PNG\r\n\x1a\n"

    missing = auth_client.get(
        f"/api/jobs/{job['id']}/results/"
        "00000000-0000-0000-0000-000000000000/image"
    )
    assert missing.status_code == 404


def test_upload_images(auth_client):
    import io

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (32, 32), (10, 120, 10)).save(buf, format="PNG")
    buf.seek(0)
    r = auth_client.post(
        "/api/jobs/upload",
        files={"files": ("cell.png", buf, "image/png")},
    )
    assert r.status_code == 201, r.text
    assert r.json()["num_images"] == 1


def test_upload_rejects_non_image(auth_client):
    r = auth_client.post(
        "/api/jobs/upload",
        files={"files": ("notes.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 400


def test_storage_and_tier_endpoints(auth_client):
    assert auth_client.get("/api/user/storage").status_code == 200
    tl = auth_client.get("/api/user/tier-limits")
    assert tl.status_code == 200
    assert "free" in tl.json()["all_tiers"]
