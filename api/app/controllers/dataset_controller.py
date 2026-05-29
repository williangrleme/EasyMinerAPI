from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.errors import ValidationError
from app.common.responses import success_payload
from app.schemas.dataset import (DatasetCreateSchema, DatasetReadSchema,
                                 DatasetUpdateSchema)

dataset_bp = Blueprint("datasets", __name__)


@dataset_bp.get("/")
@login_required
@handle_errors
def list_datasets():
    """Lista bases de dados do usuário autenticado.
    ---
    tags:
      - Datasets
    responses:
      200:
        description: Bases de dados recuperadas com sucesso
      401:
        description: Não autorizado
    """
    datasets = current_app.services["dataset"].list(current_user.id)
    data = [DatasetReadSchema.model_validate(d).model_dump() for d in datasets]
    body, status = success_payload("Bases de dados recuperadas com sucesso!", data)
    return jsonify(body), status


@dataset_bp.get("/<int:dataset_id>")
@login_required
@handle_errors
def get_dataset(dataset_id):
    """Retorna uma base de dados pelo ID.
    ---
    tags:
      - Datasets
    responses:
      200:
        description: Base de dados recuperada com sucesso
      401:
        description: Não autorizado
      404:
        description: Base de dados não encontrada
    """
    dataset = current_app.services["dataset"].get(dataset_id, current_user.id)
    body, status = success_payload(
        "Base de dados recuperada com sucesso!", DatasetReadSchema.model_validate(dataset).model_dump()
    )
    return jsonify(body), status


@dataset_bp.post("/create-dataset")
@login_required
@handle_errors
def create_dataset():
    """Cria uma nova base de dados (upload de CSV).
    ---
    tags:
      - Datasets
    requestBody:
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              csv_file:
                type: string
                format: binary
              name:
                type: string
              project_id:
                type: integer
    responses:
      201:
        description: Base de dados criada com sucesso
      401:
        description: Não autorizado
      422:
        description: Dados inválidos
    """
    csv_file = request.files.get("csv_file")
    if not csv_file:
        raise ValidationError("Dados inválidos!", {"csv_file": ["O campo é obrigatório."]})
    data = DatasetCreateSchema.model_validate(request.form.to_dict())
    dataset = current_app.services["dataset"].create(data, csv_file, current_user.id)
    body, status = success_payload(
        "Base de dados criada com sucesso!", DatasetReadSchema.model_validate(dataset).model_dump(), status=201
    )
    return jsonify(body), status


@dataset_bp.put("/<int:dataset_id>")
@login_required
@handle_errors
def update_dataset(dataset_id):
    """Atualiza uma base de dados pelo ID.
    ---
    tags:
      - Datasets
    requestBody:
      content:
        multipart/form-data:
          schema:
            type: object
            properties:
              csv_file:
                type: string
                format: binary
              name:
                type: string
    responses:
      200:
        description: Base de dados atualizada com sucesso
      401:
        description: Não autorizado
      404:
        description: Base de dados não encontrada
    """
    data = DatasetUpdateSchema.model_validate(request.form.to_dict())
    csv_file = request.files.get("csv_file")
    dataset = current_app.services["dataset"].update(dataset_id, data, csv_file, current_user.id)
    body, status = success_payload(
        "Base de dados atualizada com sucesso!", DatasetReadSchema.model_validate(dataset).model_dump()
    )
    return jsonify(body), status


@dataset_bp.delete("/<int:dataset_id>")
@login_required
@handle_errors
def delete_dataset(dataset_id):
    """Remove uma base de dados pelo ID.
    ---
    tags:
      - Datasets
    responses:
      200:
        description: Base de dados deletada com sucesso
      401:
        description: Não autorizado
      404:
        description: Base de dados não encontrada
    """
    dataset = current_app.services["dataset"].delete(dataset_id, current_user.id)
    body, status = success_payload(
        "Base de dados deletada com sucesso!", DatasetReadSchema.model_validate(dataset).model_dump()
    )
    return jsonify(body), status
