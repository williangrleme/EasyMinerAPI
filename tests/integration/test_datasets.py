import io

from tests.factories import make_dataset, make_project, make_user


def _csv_file():
    return (io.BytesIO(b"a,b\n1,2\n3,4\n"), "data.csv")


def test_list_datasets(auth_client):
    client, user = auth_client
    project = make_project(user)
    make_dataset(user, project, name="Base Um")
    resp = client.get("/api/datasets/")
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 1


def test_get_dataset(auth_client):
    client, user = auth_client
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.get(f"/api/datasets/{ds.id}")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["id"] == ds.id


def test_get_dataset_not_found(auth_client):
    client, _ = auth_client
    assert client.get("/api/datasets/9999").status_code == 404


def test_create_dataset(auth_client, s3):
    client, user = auth_client
    project = make_project(user)
    data = {"name": "Nova Base", "description": "descricao valida aqui", "project_id": str(project.id),
            "csv_file": _csv_file()}
    resp = client.post("/api/datasets/create-dataset", data=data, content_type="multipart/form-data")
    assert resp.status_code == 201
    assert resp.get_json()["data"]["name"] == "Nova Base"


def test_create_dataset_invalid_project(auth_client, s3):
    client, _ = auth_client
    data = {"name": "Nova Base", "project_id": "9999", "csv_file": _csv_file()}
    resp = client.post("/api/datasets/create-dataset", data=data, content_type="multipart/form-data")
    assert resp.status_code == 422


def test_update_duplicate_name(auth_client, s3):
    client, user = auth_client
    project = make_project(user)
    make_dataset(user, project, name="Base Existente")
    target = make_dataset(user, project, name="Base Alvo")
    resp = client.put(
        f"/api/datasets/{target.id}",
        data={"name": "Base Existente"},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 422


def test_update_to_unowned_project(auth_client, s3):
    client, user = auth_client
    project = make_project(user)
    ds = make_dataset(user, project)
    other = make_user(email="outro@test.com", phone="11900000001")
    other_project = make_project(other, name="Projeto Alheio")
    resp = client.put(
        f"/api/datasets/{ds.id}",
        data={"project_id": str(other_project.id)},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 422


def test_delete_dataset(auth_client, s3):
    client, user = auth_client
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.delete(f"/api/datasets/{ds.id}")
    assert resp.status_code == 200
    assert client.get(f"/api/datasets/{ds.id}").status_code == 404


def test_requires_login(client, db):
    assert client.get("/api/datasets/").status_code == 401
