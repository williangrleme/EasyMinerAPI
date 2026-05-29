from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.user import UserCreateSchema, UserReadSchema, UserUpdateSchema

user_bp = Blueprint("users", __name__)


@user_bp.post("/")
@handle_errors
def create_user():
    """Cria um novo usuário.
    ---
    tags:
      - Users
    requestBody:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserCreateSchema'
    responses:
      201:
        description: Usuário criado com sucesso
      422:
        description: Dados inválidos
    """
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
    """Atualiza dados do usuário autenticado.
    ---
    tags:
      - Users
    requestBody:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/UserUpdateSchema'
    responses:
      200:
        description: Usuário atualizado com sucesso
      401:
        description: Não autorizado
      422:
        description: Dados inválidos
    """
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
    """Remove o usuário autenticado.
    ---
    tags:
      - Users
    responses:
      200:
        description: Usuário deletado com sucesso
      401:
        description: Não autorizado
    """
    user = current_app.services["user"].delete(current_user.id)
    body, status = success_payload(
        "Usuário deletado com sucesso!", UserReadSchema.model_validate(user).model_dump()
    )
    return jsonify(body), status
