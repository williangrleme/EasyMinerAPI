import hashlib
import os

import app.response_handlers as response
from flask_login import current_user
import logging
from flask import request

from .. import db
from ..controllers.s3_controller import S3Controller
from ..forms.dataset_form import DatasetFormCreate, DatasetFormUpdate
from ..models import Dataset


def format_dataset_data(dataset, clean_dataset_info=None):
    dataset_info = {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "size_file": dataset.size_file,
        "file_url": dataset.file_url,
        "project_id": dataset.project_id,
    }
    if clean_dataset_info:
        dataset_info["clean_dataset"] = clean_dataset_info
    return dataset_info


def format_clean_dataset_data(clean_dataset):
    return (
        {
            "id": clean_dataset.id,
            "size_file": clean_dataset.size_file,
            "file_url": clean_dataset.file_url,
        }
        if clean_dataset
        else None
    )


def get_file_size_and_url(csv_file, user_id, dataset_name):
    csv_file.seek(0, os.SEEK_END)
    size_file_with_unit = f"{round(csv_file.tell() / (1024 * 1024), 4)}MB"
    csv_file.seek(0)
    file_hash = hashlib.md5(f"{user_id}_{dataset_name}".encode("utf-8")).hexdigest()
    csv_file.filename = f"{file_hash}.csv"

    s3 = S3Controller()
    file_url = s3.upload_file_to_s3(csv_file)
    return size_file_with_unit, file_url


def get_datasets():
    logging.info(f"Obtendo dataset com metodo: {request.method}")
    logging.info(f"Headers da requisicao: {dict(request.headers)}")

    datasets = Dataset.query.filter_by(user_id=current_user.id).all()
    datasets_list = [format_dataset_data(ds) for ds in datasets]
    return response.handle_success(
        "Bases de dados recuperadas com sucesso!",
        datasets_list,
    )


def get_dataset(dataset_id):
    dataset = (
        Dataset.query.options(db.subqueryload(Dataset.clean_dataset))
        .filter_by(id=dataset_id, user_id=current_user.id)
        .first()
    )

    if dataset is None:
        return response.handle_not_found_response("Base de dados não encontrada!")

    clean_dataset_info = format_clean_dataset_data(dataset.clean_dataset)
    dataset_data = format_dataset_data(dataset, clean_dataset_info)
    return response.handle_success(
        "Base de dados recuperada com sucesso!",
        dataset_data,
    )


def create_dataset():
    logging.info(f"Criando dataset com metodo: {request.method}")
    logging.info(f"Headers da requisicao: {dict(request.headers)}")
    logging.info(f"Arquivos na requisicao: {request.files}")

    form = DatasetFormCreate()
    if not form.validate_on_submit():
        return response.handle_unprocessable_entity(form.errors)

    csv_file = form.csv_file.data
    try:
        size_file_with_unit, file_url = get_file_size_and_url(
            csv_file, current_user.id, form.name.data
        )
        if file_url is None:
            return response.handle_internal_server_error_response(
                message="Erro ao realizar upload para o S3"
            )

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
        dataset_data = format_dataset_data(new_dataset)
        return response.handle_success(
            "Base de dados criada com sucesso!",
            dataset_data,
        )
    except Exception as e:
        db.session.rollback()
        response.log_error("Erro ao criar base de dados", e)
        return response.handle_internal_server_error_response(
            error=e, message="Erro ao criar a base de dados"
        )


def update_dataset(dataset_id):
    dataset = Dataset.query.get(dataset_id)
    if dataset is None or dataset.user_id != current_user.id:
        return response.handle_not_found_response("Base de dados não encontrada!")

    form = DatasetFormUpdate(dataset.id)
    if not form.validate_on_submit():
        return response.handle_unprocessable_entity(form.errors)

    try:
        if form.csv_file.data:
            csv_file = form.csv_file.data
            size_file_with_unit, file_url = get_file_size_and_url(
                csv_file, current_user.id, form.name.data
            )
            if file_url is None:
                return response.handle_internal_server_error_response(
                    message="Erro ao realizar upload para o S3"
                )
            dataset.size_file = size_file_with_unit
            dataset.file_url = file_url

        dataset.name = form.name.data or dataset.name
        dataset.description = form.description.data or dataset.description
        dataset.project_id = form.project_id.data or dataset.project_id

        db.session.commit()
        dataset_data = format_dataset_data(dataset)
        return response.handle_success(
            "Base de dados atualizada com sucesso!",
            dataset_data,
        )
    except Exception as e:
        db.session.rollback()
        response.log_error("Erro ao atualizar base de dados", e)
        return response.handle_internal_server_error_response(
            error=e, message="Erro ao atualizar a base de dados"
        )


def delete_dataset(dataset_id):
    dataset = Dataset.query.get(dataset_id)
    if dataset is None or dataset.user_id != current_user.id:
        return response.handle_not_found_response("Base de dados não encontrada!")

    try:
        if dataset.file_url:
            s3 = S3Controller()
            if not s3.delete_file_from_s3(dataset.file_url):
                return response.handle_internal_server_error_response(
                    message="Erro ao realizar exclusão no servidor AWS"
                )
        db.session.delete(dataset)
        db.session.commit()
        dataset_data = format_dataset_data(dataset)
        return response.handle_success(
            "Base de dados deletada com sucesso!",
            dataset_data,
        )
    except Exception as e:
        db.session.rollback()
        response.log_error("Erro ao deletar base de dados", e)
        return response.handle_internal_server_error_response(
            error=e, message="Erro ao deletar a base de dados"
        )
