from tests.factories import make_user


def test_create_user_success(client, db):
    payload = {"name": "Novo Usuario Teste", "phone_number": "11988887777",
               "email": "novo@test.com", "password": "senha1234"}
    resp = client.post("/api/users/", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["data"]["email"] == "novo@test.com"
    assert "password_hash" not in resp.get_json()["data"]


def test_create_user_duplicate_email(client, db):
    make_user(email="dup@test.com")
    payload = {"name": "Outro Usuario Teste", "phone_number": "11911112222",
               "email": "dup@test.com", "password": "senha1234"}
    resp = client.post("/api/users/", json=payload)
    assert resp.status_code == 422


def test_create_user_invalid(client, db):
    resp = client.post("/api/users/", json={"name": "x", "email": "bad", "phone_number": "1", "password": "1"})
    assert resp.status_code == 422


def test_update_user(auth_client):
    client, user = auth_client
    resp = client.put("/api/users/", json={"name": "Nome Atualizado Teste"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["name"] == "Nome Atualizado Teste"


def test_update_requires_login(client, db):
    resp = client.put("/api/users/", json={"name": "Nome Atualizado Teste"})
    assert resp.status_code == 401


def test_delete_user(auth_client):
    client, _ = auth_client
    resp = client.delete("/api/users/")
    assert resp.status_code == 200
