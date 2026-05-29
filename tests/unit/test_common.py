from app.common.errors import DomainError, NotFoundError, ValidationError, UnauthorizedError
from app.common.responses import success_payload, error_payload


def test_domain_error_default_status():
    assert DomainError("x").status == 400

def test_not_found_status():
    assert NotFoundError("nao achei").status == 404
    assert str(NotFoundError("nao achei")) == "nao achei"

def test_validation_error_carries_details():
    err = ValidationError("invalido", details={"name": ["obrigatorio"]})
    assert err.status == 422
    assert err.details == {"name": ["obrigatorio"]}

def test_unauthorized_status():
    assert UnauthorizedError("nope").status == 401

def test_success_payload_shape():
    body, status = success_payload("ok", {"id": 1})
    assert status == 200
    assert body == {"success": True, "message": "ok", "data": {"id": 1}}

def test_success_payload_custom_status():
    body, status = success_payload("criado", {"id": 1}, status=201)
    assert status == 201

def test_error_payload_shape():
    body, status = error_payload("falhou", status=404, errors={"x": ["y"]})
    assert status == 404
    assert body == {"success": False, "message": "falhou", "errors": {"x": ["y"]}}
