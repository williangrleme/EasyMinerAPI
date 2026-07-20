def test_apispec_json_available(client):
    resp = client.get("/apispec.json")
    assert resp.status_code == 200
    spec = resp.get_json()
    # o Swagger UI rejeita specs com "swagger" e "openapi" simultaneamente
    assert spec.get("openapi") == "3.0.0"
    assert "swagger" not in spec
    schemas = spec["components"]["schemas"]
    # schemas are generated from the Pydantic models
    assert "LoginSchema" in schemas
    assert "ProjectCreateSchema" in schemas
    assert "DatasetReadSchema" in schemas


def test_swagger_ui_available(client):
    resp = client.get("/apidocs/")
    assert resp.status_code == 200
