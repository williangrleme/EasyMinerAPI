from tests.factories import make_project, make_dataset


def test_list_projects(auth_client):
    client, user = auth_client
    make_project(user, name="Projeto Um")
    make_project(user, name="Projeto Dois")
    resp = client.get("/api/projects/")
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 2


def test_get_project_with_datasets(auth_client):
    client, user = auth_client
    project = make_project(user)
    make_dataset(user, project)
    resp = client.get(f"/api/projects/{project.id}")
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]["datasets"]) == 1


def test_get_project_not_found(auth_client):
    client, _ = auth_client
    resp = client.get("/api/projects/9999")
    assert resp.status_code == 404


def test_create_project(auth_client):
    client, _ = auth_client
    resp = client.post("/api/projects/", json={"name": "Novo Projeto", "description": "uma descricao valida"})
    assert resp.status_code == 201
    assert resp.get_json()["data"]["name"] == "Novo Projeto"


def test_create_duplicate_name(auth_client):
    client, user = auth_client
    make_project(user, name="Repetido")
    resp = client.post("/api/projects/", json={"name": "Repetido"})
    assert resp.status_code == 422


def test_update_project(auth_client):
    client, user = auth_client
    project = make_project(user)
    resp = client.put(f"/api/projects/{project.id}", json={"name": "Nome Novo"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["name"] == "Nome Novo"


def test_delete_project(auth_client):
    client, user = auth_client
    project = make_project(user)
    resp = client.delete(f"/api/projects/{project.id}")
    assert resp.status_code == 200


def test_requires_login(client, db):
    assert client.get("/api/projects/").status_code == 401
