from io import BytesIO

import app.response_handlers as response
import pandas as pd
from app import db
from app.controllers.s3_controller import S3Controller
from app.forms.data_mining_forms.preprocessing.data_cleaning_forms import \
    DataCleaningForm
from app.models import CleanDataset, Dataset
from flask_login import current_user


def remove_existing_clean_dataset(existing_clean_dataset):
    try:
        s3 = S3Controller()
        s3.delete_file_from_s3(existing_clean_dataset.file_url)
        db.session.delete(existing_clean_dataset)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def format_clean_dataset_data(clean_dataset):
    return {
        "clean_dataset": {
            "id": clean_dataset.id,
            "size_file": clean_dataset.size_file,
            "file_url": clean_dataset.file_url,
        }
    }


def clean_dataframe(dataset_file_url, features, missing_values, methods):
    df_original = pd.read_csv(dataset_file_url)
    df_features = df_original[features].copy()
    columns_missing_value = identify_columns_with_missing_values(
        df_features, missing_values
    )

    for column in columns_missing_value:
        update_missing_values(df_features, column, methods, missing_values)

    for col in df_features.columns:
        if df_features[col].dtype != df_original[col].dtype:
            try:
                df_features[col] = df_features[col].astype(df_original[col].dtype)
            except ValueError:
                response.internal_server_error(
                    "Erro ao converter os valores para os tipos originais!"
                )

    df_original.update(df_features)
    return df_original


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


def data_cleaning(dataset_id):
    try:
        dataset = (
            Dataset.query.with_entities(Dataset.id, Dataset.file_url)
            .filter_by(id=dataset_id, user_id=current_user.id)
            .first()
        )
        if not dataset:
            return response.handle_not_found_response("Base de dados não encontrada!")

        form = DataCleaningForm(file_url=dataset.file_url)
        if not form.validate_on_submit():
            return response.handle_unprocessable_entity(form.errors)

        df_original = clean_dataframe(
            dataset.file_url,
            form.features.data,
            form.missing_values.data,
            form.methods.data,
        )
        file_url, size_file_with_unit = save_clean_dataset(
            df_original, dataset.file_url
        )

        existing_clean_dataset = CleanDataset.query.filter_by(
            dataset_id=dataset.id
        ).first()
        if existing_clean_dataset:
            remove_existing_clean_dataset(existing_clean_dataset)

        clean_dataset = save_clean_dataset_info(
            file_url, size_file_with_unit, dataset.id
        )
        clean_dataset_data = format_clean_dataset_data(clean_dataset)

        return response.handle_success(
            "Limpeza de dados realizada com sucesso!", clean_dataset_data
        )

    except Exception as e:
        return response.handle_internal_server_error_response(
            e, "Erro ao realizar a limpeza de dados!"
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
    df[column] = df[column].replace(missing_value, pd.NA)

    if method == "mediana":
        df[column] = df[column].fillna(df[column].median().round(4))
    elif method == "media":
        df[column] = df[column].fillna(df[column].mean().round(4))
    elif method == "moda":
        df[column] = df[column].fillna(df[column].mode()[0])

    df[column] = df[column].infer_objects(copy=False)

    try:
        df[column] = pd.to_numeric(df[column])
    except ValueError:
        return response.internal_server_error(
            "Erro ao converter os valores para numéricos!"
        )


def save_clean_dataset(df, original_file_url):
    file_name_with_extension = original_file_url.split("/")[-1]
    file_name = file_name_with_extension.split(".")[0]
    clean_file_name = f"{file_name}_clean.csv"

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, header=True, index=False)
    csv_buffer.seek(0)

    size_file_with_unit = f"{round(csv_buffer.getbuffer().nbytes / (1024 * 1024), 4)}MB"

    csv_file = BytesIO(csv_buffer.read())
    csv_file.filename = clean_file_name
    csv_file.content_type = "text/csv"

    s3 = S3Controller()
    file_url = s3.upload_file_to_s3(csv_file)

    return file_url, size_file_with_unit
