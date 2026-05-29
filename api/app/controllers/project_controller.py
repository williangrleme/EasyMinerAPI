from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.project import (ProjectCreateSchema, ProjectDetailSchema,
                                 ProjectReadSchema, ProjectUpdateSchema)

project_bp = Blueprint("projects", __name__)


@project_bp.get("/")
@login_required
@handle_errors
def list_projects():
    """Lista projetos do usuário autenticado.
    ---
    tags:
      - Projects
    responses:
      200:
        description: Projetos recuperados com sucesso
      401:
        description: Não autorizado
    """
    projects = current_app.services["project"].list(current_user.id)
    data = [ProjectReadSchema.model_validate(p).model_dump() for p in projects]
    body, status = success_payload("Projetos recuperados com sucesso!", data)
    return jsonify(body), status


@project_bp.get("/<int:project_id>")
@login_required
@handle_errors
def get_project(project_id):
    """Retorna um projeto pelo ID.
    ---
    tags:
      - Projects
    responses:
      200:
        description: Projeto recuperado com sucesso
      401:
        description: Não autorizado
      404:
        description: Projeto não encontrado
    """
    project = current_app.services["project"].get(project_id, current_user.id)
    body, status = success_payload(
        "Projeto recuperado com sucesso!", ProjectDetailSchema.model_validate(project).model_dump()
    )
    return jsonify(body), status


@project_bp.post("/")
@login_required
@handle_errors
def create_project():
    """Cria um novo projeto.
    ---
    tags:
      - Projects
    requestBody:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProjectCreateSchema'
    responses:
      201:
        description: Projeto criado com sucesso
      401:
        description: Não autorizado
      422:
        description: Dados inválidos
    """
    data = ProjectCreateSchema.model_validate(request.get_json(silent=True) or {})
    project = current_app.services["project"].create(data, current_user.id)
    body, status = success_payload(
        "Projeto criado com sucesso!", ProjectReadSchema.model_validate(project).model_dump(), status=201
    )
    return jsonify(body), status


@project_bp.put("/<int:project_id>")
@login_required
@handle_errors
def update_project(project_id):
    """Atualiza um projeto pelo ID.
    ---
    tags:
      - Projects
    requestBody:
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ProjectUpdateSchema'
    responses:
      200:
        description: Projeto atualizado com sucesso
      401:
        description: Não autorizado
      404:
        description: Projeto não encontrado
    """
    data = ProjectUpdateSchema.model_validate(request.get_json(silent=True) or {})
    project = current_app.services["project"].update(project_id, data, current_user.id)
    body, status = success_payload(
        "Projeto atualizado com sucesso!", ProjectReadSchema.model_validate(project).model_dump()
    )
    return jsonify(body), status


@project_bp.delete("/<int:project_id>")
@login_required
@handle_errors
def delete_project(project_id):
    """Remove um projeto pelo ID.
    ---
    tags:
      - Projects
    responses:
      200:
        description: Projeto deletado com sucesso
      401:
        description: Não autorizado
      404:
        description: Projeto não encontrado
    """
    project = current_app.services["project"].delete(project_id, current_user.id)
    body, status = success_payload(
        "Projeto deletado com sucesso!", ProjectReadSchema.model_validate(project).model_dump()
    )
    return jsonify(body), status
