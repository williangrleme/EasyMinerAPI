from app import db
from app.controllers.s3_controller import S3Controller
from app.models import CleanDataset, Dataset
from api.app.forms.data_mining_forms.preprocessing.data_normalization_forms import (
    DataNormalizationForm,
)
from collections import OrderedDict
from flask import Response
from flask_login import current_user
import json
import pandas as pd
from io import BytesIO
from sklearn.preprocessing import MinMaxScaler, StandardScaler


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


def data_normalization(dataset_id):
    dataset = Dataset.query.filter_by(id=dataset_id, user_id=current_user.id).first()
    if not dataset:
        return create_response(
            "Base de dados não encontrada!",
            False,
            None,
            404,
        )

    file_url = dataset.file_url
    existing_clean_dataset = CleanDataset.query.filter_by(dataset_id=dataset.id).first()

    if existing_clean_dataset:
        file_url = existing_clean_dataset.file_url

    form = DataNormalizationForm(file_url=file_url)
    if not form.validate_on_submit():
        return create_response(
            "Dados inválidos!",
            False,
            form.errors,
            422,
        )

    df = pd.read_csv(file_url)
    features = form.features.data
    methods = form.methods.data

    for feature in features:
        df[feature] = normalize_data(df[feature], methods)

    file_url_normalized, size_file_with_unit = save_normalized_dataset(df, file_url)

    if existing_clean_dataset:
        s3 = S3Controller()
        s3.delete_file_from_s3(existing_clean_dataset.file_url)
        db.session.delete(existing_clean_dataset)
        db.session.commit()

    clean_dataset = CleanDataset(
        size_file=size_file_with_unit,
        file_url=file_url_normalized,
        dataset_id=dataset.id,
        user_id=current_user.id,
    )

    db.session.add(clean_dataset)
    db.session.commit()

    clean_dataset_data = {
        "id": clean_dataset.id,
        "size_file": clean_dataset.size_file,
        "file_url": clean_dataset.file_url,
        "original_dataset_id": clean_dataset.dataset_id,
    }

    return create_response(
        "Normalização de dados realizada com sucesso!",
        True,
        clean_dataset_data,
        200,
    )


def normalize_data(column, method):
    scalers = {
        "minmax": MinMaxScaler(),
        "zscore": StandardScaler(),
    }
    scaler = scalers.get(method)
    normalized_column = scaler.fit_transform(column.values.reshape(-1, 1))
    return pd.Series(normalized_column.flatten(), index=column.index).round(4)


def save_normalized_dataset(df, original_file_url):
    file_hash = original_file_url.split("/")[-1].split("_", 1)[0]
    normalized_file_name = f"{file_hash}_normalized.csv"

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    size_file_with_unit = f"{round(csv_buffer.getbuffer().nbytes / (1024 * 1024), 4)}MB"
    csv_file = BytesIO(csv_buffer.read())
    csv_file.filename = normalized_file_name
    csv_file.content_type = "text/csv"

    s3 = S3Controller()
    file_url = s3.upload_file_to_s3(csv_file)

    return file_url, size_file_with_unit
