from tests.factories import make_user


def test_login_success(client, db):
    make_user(email="a@test.com", password="senha1234")
    resp = client.post("/api/auth/login", json={"email": "a@test.com", "password": "senha1234"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["email"] == "a@test.com"
    assert "password_hash" not in body["data"]


def test_login_invalid_credentials(client, db):
    make_user(email="a@test.com", password="senha1234")
    resp = client.post("/api/auth/login", json={"email": "a@test.com", "password": "errada"})
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


def test_login_invalid_payload(client, db):
    resp = client.post("/api/auth/login", json={"email": "naoemail"})
    assert resp.status_code == 422


def test_me_requires_login(client, db):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(auth_client):
    client, user = auth_client
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["email"] == user.email


def test_logout(auth_client):
    client, _ = auth_client
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
