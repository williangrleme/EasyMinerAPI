from io import BytesIO

import app.response_handlers as response
import pandas as pd
from app import db
from app.controllers.s3_controller import S3Controller
from app.models import CleanDataset, Dataset
from flask_login import current_user
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from api.app.forms.data_mining_forms.preprocessing.data_normalization_forms import (
    DataNormalizationForm,
)


def remove_existing_clean_dataset(existing_clean_dataset):
    try:
        s3 = S3Controller()
        s3.delete_file_from_s3(existing_clean_dataset.file_url)
        db.session.delete(existing_clean_dataset)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def format_normalized_dataset_data(clean_dataset):
    return {
        "normalized_dataset": {
            "id": clean_dataset.id,
            "size_file": clean_dataset.size_file,
            "file_url": clean_dataset.file_url,
            "original_dataset_id": clean_dataset.dataset_id,
        }
    }


def save_clean_dataset_info(file_url, size_file_with_unit, dataset_id):
    try:
        clean_dataset = CleanDataset(
            size_file=size_file_with_unit,
            file_url=file_url,
            dataset_id=dataset_id,
            user_id=current_user.id,
        )
        db.session.add(clean_dataset)
        db.session.commit()
        return clean_dataset
    except Exception as e:
        db.session.rollback()
        raise e


def data_normalization(dataset_id):
    try:
        dataset = Dataset.query.filter_by(
            id=dataset_id, user_id=current_user.id
        ).first()
        if not dataset:
            return response.handle_not_found_response("Base de dados não encontrada!")

        file_url = dataset.file_url
        existing_clean_dataset = CleanDataset.query.filter_by(
            dataset_id=dataset.id
        ).first()

        if existing_clean_dataset:
            file_url = existing_clean_dataset.file_url

        form = DataNormalizationForm(file_url=file_url)
        if not form.validate_on_submit():
            return response.handle_unprocessable_entity(form.errors)

        df = pd.read_csv(file_url)
        features = form.features.data
        methods = form.methods.data

        try:
            for feature in features:
                df[feature] = normalize_data(df[feature], methods)
        except Exception as e:
            return response.handle_internal_server_error_response(
                e, "Erro ao normalizar os dados!"
            )

        file_url_normalized, size_file_with_unit = save_normalized_dataset(df, file_url)

        if existing_clean_dataset:
            remove_existing_clean_dataset(existing_clean_dataset)

        clean_dataset = save_clean_dataset_info(
            file_url_normalized, size_file_with_unit, dataset.id
        )
        clean_dataset_data = format_normalized_dataset_data(clean_dataset)

        return response.handle_success(
            "Normalização de dados realizada com sucesso!", clean_dataset_data
        )

    except Exception as e:
        return response.handle_internal_server_error_response(
            e, "Erro ao realizar a normalização de dados!"
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
    file_name_with_extension = original_file_url.split("/")[-1]
    file_name = file_name_with_extension.split(".")[0]
    file_name = file_name.split("_")[0]

    normalized_file_name = f"{file_name}_normalized.csv"

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
