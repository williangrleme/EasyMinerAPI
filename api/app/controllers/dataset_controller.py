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
    if not current_user.is_authenticated:
        return (
            jsonify(
                {
                    "message": "Não autorizado!",
                    "success": False,
                    "data": None,
                }
            ),
            403,
        )

    datasets = (
        Dataset.query.options(subqueryload(Dataset.clean_dataset))
        .filter_by(user_id=current_user.id)
        .all()
    )

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

    return (
        jsonify(
            {
                "message": "Bases de dados recuperadas com sucesso!",
                "success": True,
                "data": datasets_list,
            }
        ),
        200,
    )


def get_dataset(id):
    if not current_user.is_authenticated:
        return (
            jsonify(
                {
                    "message": "Não autorizado!",
                    "success": False,
                    "data": None,
                }
            ),
            403,
        )

    dataset = (
        Dataset.query.options(subqueryload(Dataset.clean_dataset))
        .filter_by(id=id, user_id=current_user.id)
        .first()
    )

    if dataset is None:
        return (
            jsonify(
                {
                    "message": "Base de dados não encontrada!",
                    "success": False,
                    "data": None,
                }
            ),
            404,
        )

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

    dataset_data = {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "size_file": dataset.size_file,
        "file_url": dataset.file_url,
        "clean_dataset": clean_data,
    }

    return (
        jsonify(
            {
                "message": "Base de dados recuperada com sucesso!",
                "success": True,
                "data": dataset_data,
            }
        ),
        200,
    )


def create_dataset():
    if not current_user.is_authenticated:
        return (
            jsonify(
                {
                    "message": "Não autorizado!",
                    "success": False,
                    "data": None,
                }
            ),
            403,
        )

    form = DatasetFormCreate()
    if form.validate_on_submit():
        csv_file = form.csv_file.data

        csv_file.seek(0, os.SEEK_END)
        size_file_with_unit = f"{round(csv_file.tell() / (1024 * 1024), 4)}MB"
        csv_file.seek(0)

        file_hash = hashlib.md5(
            f"{current_user.id}_{form.name.data}".encode("utf-8")
        ).hexdigest()
        csv_file.filename = f"{file_hash}.csv"

        s3Controller = S3Controller()
        file_url = s3Controller.upload_file_to_s3(csv_file)

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
        dataset_data = {
            "id": new_dataset.id,
            "name": new_dataset.name,
            "description": new_dataset.description,
            "size_file": new_dataset.size_file,
            "file_url": new_dataset.file_url,
        }
        return (
            jsonify(
                {
                    "message": "Base de dados criada com sucesso!",
                    "success": True,
                    "data": dataset_data,
                }
            ),
            201,
        )

    return (
        jsonify(
            {
                "message": "Dados inválidos!",
                "success": False,
                "data": form.errors,
            }
        ),
        422,
    )


def update_dataset(id):
    if not current_user.is_authenticated:
        return (
            jsonify(
                {
                    "message": "Não autorizado!",
                    "success": False,
                    "data": None,
                }
            ),
            403,
        )

    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return (
            jsonify(
                {
                    "message": "Base de dados não encontrada!",
                    "success": False,
                    "data": None,
                }
            ),
            404,
        )

    form = DatasetFormUpdate(dataset.id)
    if form.validate_on_submit():
        s3Controller = S3Controller()

        if form.csv_file.data:
            csv_file = form.csv_file.data

            csv_file.seek(0, os.SEEK_END)
            size_file_with_unit = f"{round(csv_file.tell() / (1024 * 1024), 4)}MB"
            csv_file.seek(0)

            file_hash = hashlib.md5(
                f"{current_user.id}_{form.name.data}".encode("utf-8")
            ).hexdigest()
            csv_file.filename = f"{file_hash}.csv"

            file_url = s3Controller.upload_file_to_s3(csv_file)
            dataset.size_file = size_file_with_unit
            dataset.file_url = file_url

        dataset.name = form.name.data or dataset.name
        dataset.description = form.description.data or dataset.description
        dataset.project_id = form.project_id.data or dataset.project_id

        db.session.commit()
        dataset_data = {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "size_file": dataset.size_file,
            "file_url": dataset.file_url,
        }
        return (
            jsonify(
                {
                    "message": "Base de dados atualizada com sucesso!",
                    "success": True,
                    "data": dataset_data,
                }
            ),
            200,
        )

    return (
        jsonify(
            {
                "message": "Dados inválidos!",
                "success": False,
                "data": form.errors,
            }
        ),
        422,
    )


def delete_dataset(id):
    if not current_user.is_authenticated:
        return (
            jsonify(
                {
                    "message": "Não autorizado!",
                    "success": False,
                    "data": None,
                }
            ),
            403,
        )

    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return (
            jsonify(
                {
                    "message": "Base de dados não encontrada!",
                    "success": False,
                    "data": None,
                }
            ),
            404,
        )

    if dataset.file_url:
        s3Controller = S3Controller()
        if not s3Controller.delete_file_from_s3(dataset.file_url):
            return (
                jsonify(
                    {
                        "message": "Credenciais inválidas para acesso ao S3.",
                        "success": False,
                        "data": None,
                    }
                ),
                403,
            )

    db.session.delete(dataset)
    db.session.commit()
    dataset_data = {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "size_file": dataset.size_file,
        "file_url": dataset.file_url,
    }
    return (
        jsonify(
            {
                "message": "Base de dados deletada com sucesso!",
                "success": True,
                "data": dataset_data,
            }
        ),
        200,
    )
