import pandas as pd
from io import BytesIO
from flask_login import current_user
from flask import jsonify
from app.models import Dataset
from api.app.forms.data_mining_forms.preprocessing.data_normalization_forms import (
    DataNormalizationForm,
)
from app.controllers.s3_controller import S3Controller
from app import db
from sklearn.preprocessing import MinMaxScaler, StandardScaler


def data_normalization(id):
    dataset = Dataset.query.filter_by(id=id, user_id=current_user.id).first()
    if not dataset:
        return (
            jsonify(
                {
                    "message": "Base de dados não encontrada!",
                    "data": None,
                    "success": False,
                }
            ),
            404,
        )

    clean_dataset = dataset.clean_dataset
    form = DataNormalizationForm(file_url=clean_dataset.file_url)
    if not form.validate_on_submit():
        return (
            jsonify(
                {
                    "message": "Dados inválidos!",
                    "data": form.errors,
                    "success": False,
                }
            ),
            422,
        )

    df_original = pd.read_csv(clean_dataset.file_url)
    features = form.features.data
    methods = form.methods.data

    for feature in features:
        df_original[feature] = normalize_data(df_original[feature], methods)

    file_url, size_file_with_unit = save_normalized_dataset(
        df_original, clean_dataset.file_url
    )
    clean_dataset.file_url = file_url
    clean_dataset.size_file = size_file_with_unit
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Normalização de dados realizada com sucesso!",
                "data": None,
                "success": True,
            }
        ),
        200,
    )


def normalize_data(column, method):
    scalers = {"minmax": MinMaxScaler(), "zscore": StandardScaler()}
    scaler = scalers.get(method)
    if not scaler:
        raise ValueError(f"Método de normalização desconhecido: {method}")

    normalized_column = scaler.fit_transform(column.values.reshape(-1, 1))
    return pd.Series(normalized_column.flatten(), index=column.index)


def save_normalized_dataset(df, original_file_url):
    file_hash = (
        original_file_url.split("/")[-1].replace(".csv", "").replace("_clean", "")
    )
    normalized_file_name = f"{file_hash}_normalized.csv"

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    size_file_with_unit = f"{round(csv_buffer.getbuffer().nbytes / (1024 * 1024), 4)}MB"
    csv_file = BytesIO(csv_buffer.read())
    csv_file.filename = normalized_file_name
    csv_file.content_type = "text/csv"

    s3 = S3Controller()
    s3.delete_file_from_s3(original_file_url)
    file_url = s3.upload_file_to_s3(csv_file)

    return file_url, size_file_with_unit
