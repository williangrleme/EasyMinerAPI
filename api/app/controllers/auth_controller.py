from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.auth import LoginSchema
from app.schemas.user import UserReadSchema

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
@handle_errors
def login():
    """Realiza login do usuário.
    ---
    tags:
      - Auth
    requestBody:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/LoginSchema'
    responses:
      200:
        description: Login realizado com sucesso
      401:
        description: Credenciais inválidas
      422:
        description: Dados inválidos
    """
    if current_user.is_authenticated:
        current_app.services["auth"].logout()
    data = LoginSchema.model_validate(request.get_json(silent=True) or {})
    user = current_app.services["auth"].login(data)
    body, status = success_payload(
        "Login realizado com sucesso!", UserReadSchema.model_validate(user).model_dump()
    )
    return jsonify(body), status


@auth_bp.post("/logout")
@login_required
@handle_errors
def logout():
    """Realiza logout do usuário.
    ---
    tags:
      - Auth
    responses:
      200:
        description: Logout realizado com sucesso
      401:
        description: Não autorizado
    """
    current_app.services["auth"].logout()
    body, status = success_payload("Logout realizado com sucesso!")
    return jsonify(body), status


@auth_bp.get("/me")
@login_required
@handle_errors
def me():
    """Retorna dados do usuário autenticado.
    ---
    tags:
      - Auth
    responses:
      200:
        description: Usuário atual recuperado com sucesso
      401:
        description: Não autorizado
    """
    body, status = success_payload(
        "Usuário atual recuperado com sucesso!",
        UserReadSchema.model_validate(current_user).model_dump(),
    )
    return jsonify(body), status
