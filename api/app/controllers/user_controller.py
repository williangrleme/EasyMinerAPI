from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.user import UserCreateSchema, UserReadSchema, UserUpdateSchema

user_bp = Blueprint("users", __name__)


@user_bp.post("/")
@handle_errors
def create_user():
    data = UserCreateSchema.model_validate(request.get_json(silent=True) or {})
    user = current_app.services["user"].create(data)
    body, status = success_payload(
        "Usuário criado com sucesso!", UserReadSchema.model_validate(user).model_dump(), status=201
    )
    return jsonify(body), status


@user_bp.put("/")
@login_required
@handle_errors
def update_user():
    data = UserUpdateSchema.model_validate(request.get_json(silent=True) or {})
    user = current_app.services["user"].update(current_user.id, data)
    body, status = success_payload(
        "Usuário atualizado com sucesso!", UserReadSchema.model_validate(user).model_dump()
    )
    return jsonify(body), status


@user_bp.delete("/")
@login_required
@handle_errors
def delete_user():
    user = current_app.services["user"].delete(current_user.id)
    body, status = success_payload(
        "Usuário deletado com sucesso!", UserReadSchema.model_validate(user).model_dump()
    )
    return jsonify(body), status
