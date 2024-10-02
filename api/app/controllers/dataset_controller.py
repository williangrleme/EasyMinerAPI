import hashlib
from flask import jsonify
from flask_login import current_user
from app import db
from app.models import Dataset
from app.forms.dataset_form import DatasetFormCreate, DatasetFormUpdate
from app.controllers.s3_controller import S3Controller
import os
from sqlalchemy.orm import subqueryload


def get_datasets():
    # Verifica se o usuário está autenticado
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Consulta os datasets do usuário autenticado com o relacionamento clean_dataset
    datasets = (
        Dataset.query.options(
            subqueryload(Dataset.clean_dataset)  # Carrega a relação com CleanDataset
        )
        .filter_by(user_id=current_user.id)
        .all()
    )

    # Constrói uma lista de dicionários contendo as informações dos datasets
    datasets_list = []
    for ds in datasets:
        clean_data = None
        if ds.clean_dataset and (
            ds.clean_dataset.size_file
            or ds.clean_dataset.name
            or ds.clean_dataset.file_url
        ):
            clean_data = {
                "size_file": ds.clean_dataset.size_file,
                "file_url": ds.clean_dataset.file_url,
            }

        dataset_info = {
            "id": ds.id,
            "name": ds.name,
            "description": ds.description,
            "size_file": ds.size_file,
            "file_url": ds.file_url,
            "clean_dataset": clean_data,
        }

        datasets_list.append(dataset_info)

    return jsonify(datasets_list), 200


def get_dataset(id):
    # Verifica se o usuário está autenticado
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Consulta um dataset específico pelo id com o relacionamento clean_dataset
    dataset = (
        Dataset.query.options(
            subqueryload(Dataset.clean_dataset)  # Carrega a relação com CleanDataset
        )
        .filter_by(id=id, user_id=current_user.id)
        .first()
    )

    if dataset is None:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    # Verifica se o clean_dataset possui dados relevantes
    clean_data = None
    if dataset.clean_dataset and (
        dataset.clean_dataset.size_file
        or dataset.clean_dataset.name
        or dataset.clean_dataset.file_url
    ):
        clean_data = {
            "size_file": dataset.clean_dataset.size_file,
            "file_url": dataset.clean_dataset.file_url,
        }

    # Constrói o dicionário com as informações do dataset
    dataset_data = {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "size_file": dataset.size_file,
        "file_url": dataset.file_url,
        "clean_dataset": clean_data,  # Inclui clean_dataset apenas se houver dados válidos
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
