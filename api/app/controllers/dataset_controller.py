import hashlib
import json
import os
from collections import OrderedDict
from flask import Response
from flask_login import current_user
from sqlalchemy.orm import subqueryload
from app import db
from app.controllers.s3_controller import S3Controller
from app.forms.dataset_form import DatasetFormCreate, DatasetFormUpdate
from app.models import Dataset


def create_response(message, success, data=None, status_code=200):
    response_data = OrderedDict(
        [
            ("message", message),
            ("success", success),
            ("data", data),
        ]
    )
    response_json = json.dumps(response_data)
    return Response(response_json, mimetype="application/json", status=status_code)


def get_datasets():
    datasets = (
        Dataset.query.options(subqueryload(Dataset.clean_dataset))
        .filter_by(user_id=current_user.id)
        .all()
    )

    datasets_list = []
    for ds in datasets:
        clean_dataset_info = None
        if ds.clean_dataset and (
            ds.clean_dataset.size_file
            or ds.clean_dataset.name
            or ds.clean_dataset.file_url
        ):
            clean_dataset_info = OrderedDict(
                [
                    ("id", ds.clean_dataset.id),
                    ("size_file", ds.clean_dataset.size_file),
                    ("file_url", ds.clean_dataset.file_url),
                ]
            )
        dataset_info = OrderedDict(
            [
                ("id", ds.id),
                ("name", ds.name),
                ("description", ds.description),
                ("size_file", ds.size_file),
                ("file_url", ds.file_url),
                ("project_id", ds.project_id),
                ("clean_dataset", clean_dataset_info),
            ]
        )
        datasets_list.append(dataset_info)

    return create_response(
        "Bases de dados recuperadas com sucesso!",
        True,
        datasets_list,
        200,
    )


def get_dataset(dataset_id):
    dataset = (
        Dataset.query.options(subqueryload(Dataset.clean_dataset))
        .filter_by(id=dataset_id, user_id=current_user.id)
        .first()
    )

    if dataset is None:
        return create_response(
            "Base de dados não encontrada!",
            False,
            None,
            404,
        )

    clean_dataset_info = None
    if dataset.clean_dataset and (
        dataset.clean_dataset.size_file
        or dataset.clean_dataset.name
        or dataset.clean_dataset.file_url
    ):
        clean_dataset_info = OrderedDict(
            [
                ("id", dataset.clean_dataset.id),
                ("size_file", dataset.clean_dataset.size_file),
                ("file_url", dataset.clean_dataset.file_url),
            ]
        )

    dataset_data = OrderedDict(
        [
            ("id", dataset.id),
            ("name", dataset.name),
            ("description", dataset.description),
            ("size_file", dataset.size_file),
            ("file_url", dataset.file_url),
            ("project_id", dataset.project_id),
            ("clean_dataset", clean_dataset_info),
        ]
    )

    return create_response(
        "Base de dados recuperada com sucesso!",
        True,
        dataset_data,
        200,
    )


def create_dataset():
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

        dataset_data = OrderedDict(
            [
                ("id", new_dataset.id),
                ("name", new_dataset.name),
                ("description", new_dataset.description),
                ("size_file", new_dataset.size_file),
                ("file_url", new_dataset.file_url),
                ("project_id", new_dataset.project_id),
            ]
        )
        return create_response(
            "Base de dados criada com sucesso!",
            True,
            dataset_data,
            201,
        )

    return create_response(
        "Dados inválidos!",
        False,
        form.errors,
        422,
    )


def update_dataset(dataset_id):
    dataset = Dataset.query.get(dataset_id)
    if dataset is None or dataset.user_id != current_user.id:
        return create_response(
            "Base de dados não encontrada!",
            False,
            None,
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
        dataset_data = OrderedDict(
            [
                ("id", dataset.id),
                ("name", dataset.name),
                ("description", dataset.description),
                ("size_file", dataset.size_file),
                ("file_url", dataset.file_url),
            ]
        )
        return create_response(
            "Base de dados atualizada com sucesso!",
            True,
            dataset_data,
            200,
        )

    return create_response(
        "Dados inválidos!",
        False,
        form.errors,
        422,
    )


def delete_dataset(dataset_id):
    dataset = Dataset.query.get(dataset_id)
    if dataset is None or dataset.user_id != current_user.id:
        return create_response(
            "Base de dados não encontrada!",
            False,
            None,
            404,
        )
    if dataset.file_url:
        s3Controller = S3Controller()
        if not s3Controller.delete_file_from_s3(dataset.file_url):
            return create_response(
                "Credenciais inválidas para acesso ao S3.",
                False,
                None,
                403,
            )

    db.session.delete(dataset)
    db.session.commit()
    dataset_data = OrderedDict(
        [
            ("id", dataset.id),
            ("name", dataset.name),
            ("description", dataset.description),
            ("size_file", dataset.size_file),
            ("file_url", dataset.file_url),
        ]
    )
    return create_response(
        "Base de dados deletada com sucesso!",
        True,
        dataset_data,
        200,
    )
