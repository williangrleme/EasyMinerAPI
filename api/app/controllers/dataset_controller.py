import hashlib
from flask import jsonify
from flask_login import current_user
from app import db
from app.models import Dataset
from app.forms.dataset_form import DatasetFormCreate, DatasetFormUpdate
from app.controllers.s3_controller import S3Controller
import os


def get_datasets():
    # Verifica se o usuário está autenticado
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Consulta os datasets do usuário autenticado
    datasets = (
        Dataset.query.with_entities(
            Dataset.id,
            Dataset.name,
            Dataset.description,
            Dataset.size_file,
            Dataset.file_url,
            Dataset.project_id,
            Dataset.user_id,
        )
        .filter_by(user_id=current_user.id)
        .all()
    )

    # Constrói uma lista de dicionários contendo as informações dos datasets
    datasets_list = [
        {
            "id": ds.id,
            "name": ds.name,
            "description": ds.description,
            "size_file": ds.size_file,
            "file_url": ds.file_url,
            "project_id": ds.project_id,
        }
        for ds in datasets
    ]
    return jsonify(datasets_list), 200


def get_dataset(id):
    # Verifica se o usuário está autenticado
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Consulta um dataset específico pelo id
    dataset = (
        Dataset.query.with_entities(
            Dataset.id,
            Dataset.name,
            Dataset.description,
            Dataset.size_file,
            Dataset.file_url,
            Dataset.project_id,
            Dataset.user_id,
        )
        .filter_by(id=id, user_id=current_user.id)
        .first()
    )

    if dataset is None:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    # Constrói o dicionário com as informações do dataset
    dataset_data = {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "size_file": dataset.size_file,
        "file_url": dataset.file_url,
        "project_id": dataset.project_id,
    }
    return jsonify(dataset_data), 200


def create_dataset():
    # Verifica se o usuário está autenticado
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    form = DatasetFormCreate()
    if form.validate_on_submit():
        csv_file = form.csv_file.data

        # Calcula o tamanho do arquivo em MB
        csv_file.seek(0, os.SEEK_END)
        size_file_with_unit = f"{round(csv_file.tell() / (1024 * 1024), 4)}MB"
        csv_file.seek(0)

        # Gera um hash para o nome do arquivo com base no ID do usuário e nome do dataset
        file_hash = hashlib.md5(
            f"{current_user.id}_{form.name.data}".encode("utf-8")
        ).hexdigest()
        csv_file.filename = f"{file_hash}.csv"

        # Realiza o upload do arquivo para o S3
        s3Controller = S3Controller()
        file_url = s3Controller.upload_file_to_s3(csv_file)

        # Cria uma nova entrada de dataset no banco de dados
        new_dataset = Dataset(
            name=form.name.data,
            description=form.description.data,
            size_file=size_file_with_unit,
            project_id=form.project_id.data,
            user_id=current_user.id,
            file_url=file_url,
        )
        db.session.add(new_dataset)
        db.session.commit()
        return jsonify({"mensagem": "Base de dados criada com sucesso!"}), 201

    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def update_dataset(id):
    # Verifica se o usuário está autenticado
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Consulta o dataset a ser atualizado
    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    form = DatasetFormUpdate()
    if form.validate_on_submit():
        s3Controller = S3Controller()

        if form.csv_file.data:
            csv_file = form.csv_file.data

            # Calcula o tamanho do arquivo em MB
            csv_file.seek(0, os.SEEK_END)
            size_file_with_unit = f"{round(csv_file.tell() / (1024 * 1024), 4)}MB"
            csv_file.seek(0)

            # Gera um hash para o nome do arquivo com base no ID do usuário e nome do dataset
            file_hash = hashlib.md5(
                f"{current_user.id}_{form.name.data}".encode("utf-8")
            ).hexdigest()
            csv_file.filename = f"{file_hash}.csv"

            # Realiza o upload do arquivo atualizado para o S3
            file_url = s3Controller.upload_file_to_s3(csv_file)
            dataset.size_file = size_file_with_unit
            dataset.file_url = file_url

        # Atualiza os campos do dataset com os novos dados fornecidos
        dataset.name = form.name.data or dataset.name
        dataset.description = form.description.data or dataset.description
        dataset.project_id = form.project_id.data or dataset.project_id

        db.session.commit()
        return jsonify({"mensagem": "Base de dados atualizada com sucesso!"}), 200

    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def delete_dataset(id):
    # Verifica se o usuário está autenticado
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Consulta o dataset a ser deletado
    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    if dataset.file_url:
        s3Controller = S3Controller()
        # Deleta o arquivo do S3
        if not s3Controller.delete_file_from_s3(dataset.file_url):
            return (
                jsonify({"mensagem": "Credenciais inválidas para acesso ao S3."}),
                403,
            )

    # Deleta o dataset do banco de dados
    db.session.delete(dataset)
    db.session.commit()
    return jsonify({"mensagem": "Base de dados deletada com sucesso!"}), 200
