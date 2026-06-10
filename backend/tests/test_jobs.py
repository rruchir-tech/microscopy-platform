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


def test_storage_and_tier_endpoints(auth_client):
    assert auth_client.get("/api/user/storage").status_code == 200
    tl = auth_client.get("/api/user/tier-limits")
    assert tl.status_code == 200
    assert "free" in tl.json()["all_tiers"]
