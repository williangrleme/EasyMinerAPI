from api.app.forms.data_mining_forms.preprocessing.data_reduction_forms import (
    DataReductionForm,
)
from app import db
from app.controllers.s3_controller import S3Controller
from app.models import CleanDataset, Dataset
from collections import OrderedDict
from flask import Response
from flask_login import current_user
from io import BytesIO
import json
import pandas as pd
from sklearn.decomposition import PCA


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


def data_reduction(dataset_id):
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

    form = DataReductionForm(file_url=file_url)

    if not form.validate_on_submit():
        return create_response(
            "Dados inválidos!",
            False,
            form.errors,
            422,
        )

    df = pd.read_csv(file_url)
    features = form.features.data
    method = form.methods.data

    reduced_df = reduce_data(df, features, method, form)
    file_url_reduced, size_file_with_unit = save_reduced_dataset(reduced_df, file_url)

    if existing_clean_dataset:
        s3 = S3Controller()
        s3.delete_file_from_s3(existing_clean_dataset.file_url)
        db.session.delete(existing_clean_dataset)
        db.session.commit()

    clean_dataset = CleanDataset(
        size_file=size_file_with_unit,
        file_url=file_url_reduced,
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
        "Redução de dados realizada com sucesso!",
        True,
        clean_dataset_data,
        200,
    )


def reduce_data(df, features, method, form):
    reduction_methods = {
        "pca": apply_pca,
        "amostragem_aleatoria": random_sampling,
        "amostragem_sistematica": systematic_sampling,
    }
    reduction_method = reduction_methods.get(method)
    return reduction_method(df, features, form)


def apply_pca(df, features, form):
    pca = PCA(n_components=2)
    pca_result = pca.fit_transform(df[features])
    return pd.DataFrame(
        pca_result, columns=["Componente Principal 1", "Componente Principal 2"]
    )


def random_sampling(df, features, form):
    n = form.random_records.data
    return df.sample(n=n, replace=False)


def systematic_sampling(df, features, form):
    n = form.systematic_records.data
    systematic_method = form.systematic_method.data
    feature = features[0]

    if systematic_method == "maiores":
        return df.nlargest(n, feature)
    elif systematic_method == "menores":
        return df.nsmallest(n, feature)


def save_reduced_dataset(df, original_file_url):
    file_hash = original_file_url.split("/")[-1].split("_", 1)[0]
    reduced_file_name = f"{file_hash}_reduced.csv"

    csv_buffer = BytesIO()
    df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)

    size_file_with_unit = f"{round(csv_buffer.getbuffer().nbytes / (1024 * 1024), 4)}MB"
    csv_file = BytesIO(csv_buffer.read())
    csv_file.filename = reduced_file_name
    csv_file.content_type = "text/csv"

    s3 = S3Controller()
    file_url = s3.upload_file_to_s3(csv_file)

    return file_url, size_file_with_unit
