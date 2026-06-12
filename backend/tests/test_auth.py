def test_register_and_me(client):
    r = client.post(
        "/api/auth/register",
        json={"email": "a@example.com", "username": "alice", "password": "password123"},
    )
    assert r.status_code == 201, r.text
    tokens = r.json()
    assert tokens["access_token"] and tokens["refresh_token"]

    me = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == "a@example.com"
    assert me.json()["tier"] == "free"


def test_duplicate_email_rejected(client):
    payload = {"email": "dup@example.com", "username": "dup1", "password": "password123"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    payload2 = {**payload, "username": "dup2"}
    r = client.post("/api/auth/register", json=payload2)
    assert r.status_code == 409


def test_login_wrong_password(client):
    client.post(
        "/api/auth/register",
        json={"email": "b@example.com", "username": "bob", "password": "password123"},
    )
    r = client.post(
        "/api/auth/login", json={"email": "b@example.com", "password": "wrong"}
    )
    assert r.status_code == 401


def test_login_and_refresh(client):
    client.post(
        "/api/auth/register",
        json={"email": "c@example.com", "username": "carol", "password": "password123"},
    )
    login = client.post(
        "/api/auth/login", json={"email": "c@example.com", "password": "password123"}
    )
    assert login.status_code == 200
    refresh = client.post(
        "/api/auth/refresh", json={"refresh_token": login.json()["refresh_token"]}
    )
    assert refresh.status_code == 200
    assert refresh.json()["access_token"]


def test_protected_route_requires_token(client):
    assert client.get("/api/pipelines").status_code in (401, 403)
