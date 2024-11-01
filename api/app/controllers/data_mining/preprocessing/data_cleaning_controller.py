from app import db
from app.controllers.s3_controller import S3Controller
from app.forms.data_mining_forms.preprocessing.data_cleaning_forms import (
    DataCleaningForm,
)
from app.models import CleanDataset, Dataset
from collections import OrderedDict
from flask import Response
from flask_login import current_user
import json
import pandas as pd
from io import BytesIO


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


def data_cleaning(dataset_id):
    dataset = (
        Dataset.query.with_entities(Dataset.id, Dataset.file_url)
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

    form = DataCleaningForm(file_url=dataset.file_url)
    if form.validate_on_submit():
        features = form.features.data
        methods = form.methods.data
        missing_values = form.missing_values.data

        df_original = pd.read_csv(dataset.file_url)
        df_features = df_original[features].copy()
        columns_missing_value = identify_columns_with_missing_values(
            df_features, missing_values
        )

        for column in columns_missing_value:
            update_missing_values(df_features, column, methods, missing_values)

        df_original.update(df_features)
        file_url, size_file_with_unit = save_clean_dataset(
            df_original, dataset.file_url
        )

        clean_dataset = CleanDataset(
            size_file=size_file_with_unit,
            file_url=file_url,
            dataset_id=dataset.id,
            user_id=current_user.id,
        )

        existing_clean_dataset = CleanDataset.query.filter_by(
            dataset_id=dataset.id
        ).first()
        if existing_clean_dataset:
            s3 = S3Controller()
            s3.delete_file_from_s3(existing_clean_dataset.file_url)
            db.session.delete(existing_clean_dataset)
            db.session.commit()

        db.session.add(clean_dataset)
        db.session.commit()

        clean_dataset_data = {
            "id": clean_dataset.id,
            "size_file": clean_dataset.size_file,
            "file_url": clean_dataset.file_url,
            "original_dataset_id": clean_dataset.dataset_id,
        }

        return create_response(
            "Limpeza de dados realizada com sucesso!",
            True,
            clean_dataset_data,
            200,
        )

    return create_response(
        "Dados inválidos!",
        False,
        form.errors,
        422,
    )


def convert_missing_values(missing_values):
    mapping = {"null": None, "0": 0, "?": "?"}
    return [mapping.get(value, value) for value in missing_values]


def identify_columns_with_missing_values(df, missing_values):
    converted_missing_values = convert_missing_values(missing_values)
    columns_with_missing_values = []

    for column in df.columns:
        if (
            any(df[column].isin([value]).any() for value in converted_missing_values)
            or df[column].isna().any()
        ):
            columns_with_missing_values.append(column)
    return columns_with_missing_values


def update_missing_values(df, column, method, missing_values):
    missing_value = convert_missing_values(missing_values)
    df[column].replace(missing_value, pd.NA, inplace=True)

    if method == "mediana":
        df[column] = df[column].fillna(df[column].median().round(4))
    elif method == "media":
        df[column] = df[column].fillna(df[column].mean().round(4))
    elif method == "moda":
        df[column] = df[column].fillna(df[column].mode()[0])


def save_clean_dataset(df, original_file_url):
    file_hash = original_file_url.split("/")[-1].split("_", 1)[0]
    clean_file_name = f"{file_hash}_clean.csv"

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, header=True, index=False)
    csv_buffer.seek(0)

    size_file_with_unit = f"{round(csv_buffer.getbuffer().nbytes / (1024 * 1024), 4)}MB"

    csv_file = BytesIO(csv_buffer.read())
    csv_file.filename = clean_file_name
    csv_file.content_type = "text/csv"

    s3Controller = S3Controller()
    file_url = s3Controller.upload_file_to_s3(csv_file)

    return file_url, size_file_with_unit
