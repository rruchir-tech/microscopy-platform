VALID_CONFIG = {
    "nodes": [
        {"id": "n1", "type": "image_load", "params": {"target_size": 256}},
        {"id": "n2", "type": "thresholding", "params": {"method": "otsu"}},
        {"id": "n3", "type": "cell_detection", "params": {}},
        {"id": "n4", "type": "export_results", "params": {"include_images": False}},
    ],
    "edges": [
        {"source": "n1", "target": "n2"},
        {"source": "n2", "target": "n3"},
        {"source": "n3", "target": "n4"},
    ],
}


def test_pipeline_crud(auth_client):
    # create
    r = auth_client.post(
        "/api/pipelines",
        json={"name": "My Pipeline", "description": "d", "config": VALID_CONFIG},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    # list
    lst = auth_client.get("/api/pipelines")
    assert lst.status_code == 200
    assert any(p["id"] == pid for p in lst.json())

    # get
    got = auth_client.get(f"/api/pipelines/{pid}")
    assert got.status_code == 200
    assert got.json()["version"] == 1

    # update bumps version
    upd = auth_client.put(
        f"/api/pipelines/{pid}", json={"name": "Renamed", "config": VALID_CONFIG}
    )
    assert upd.status_code == 200
    assert upd.json()["name"] == "Renamed"
    assert upd.json()["version"] == 2

    # clone
    clone = auth_client.post(f"/api/pipelines/{pid}/clone")
    assert clone.status_code == 201
    assert clone.json()["name"].endswith("(copy)")

    # delete
    assert auth_client.delete(f"/api/pipelines/{pid}").status_code == 200
    assert auth_client.get(f"/api/pipelines/{pid}").status_code == 404


def test_invalid_config_rejected(auth_client):
    bad = {
        "nodes": [{"id": "n1", "type": "not_a_real_module", "params": {}}],
        "edges": [],
    }
    r = auth_client.post("/api/pipelines", json={"name": "bad", "config": bad})
    assert r.status_code == 422


def test_cyclic_config_rejected(auth_client):
    cyclic = {
        "nodes": [
            {"id": "n1", "type": "image_load", "params": {}},
            {"id": "n2", "type": "thresholding", "params": {}},
        ],
        "edges": [
            {"source": "n1", "target": "n2"},
            {"source": "n2", "target": "n1"},
        ],
    }
    r = auth_client.post("/api/pipelines", json={"name": "cyclic", "config": cyclic})
    assert r.status_code == 422


def test_modules_endpoint(client):
    r = client.get("/api/pipelines/modules")
    assert r.status_code == 200
    types = {m["type"] for m in r.json()}
    assert "cell_detection" in types and "export_results" in types


def test_templates_instantiate(auth_client):
    templates = auth_client.get("/api/templates")
    assert templates.status_code == 200
    tid = templates.json()[0]["id"]
    inst = auth_client.post(f"/api/templates/{tid}/instantiate")
    assert inst.status_code == 201
    assert inst.json()["name"]
