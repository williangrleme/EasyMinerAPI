from io import BytesIO

import app.response_handlers as response
import pandas as pd
from app import db
from app.controllers.s3_controller import S3Controller
from app.models import CleanDataset, Dataset
from flask_login import current_user
from sklearn.decomposition import PCA

from api.app.forms.data_mining_forms.preprocessing.data_reduction_forms import \
    DataReductionForm


def remove_existing_clean_dataset(existing_clean_dataset):
    try:
        s3 = S3Controller()
        s3.delete_file_from_s3(existing_clean_dataset.file_url)
        db.session.delete(existing_clean_dataset)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e


def format_reduced_dataset_data(clean_dataset):
    return {
        "reduced_dataset": {
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


def data_reduction(dataset_id):
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

        form = DataReductionForm(file_url=file_url)
        if not form.validate_on_submit():
            return response.handle_unprocessable_entity(form.errors)

        df = pd.read_csv(file_url)
        features = form.features.data
        method = form.methods.data

        reduced_df = reduce_data(df, features, method, form)
        file_url_reduced, size_file_with_unit = save_reduced_dataset(
            reduced_df, file_url
        )

        if existing_clean_dataset:
            remove_existing_clean_dataset(existing_clean_dataset)

        clean_dataset = save_clean_dataset_info(
            file_url_reduced, size_file_with_unit, dataset.id
        )
        clean_dataset_data = format_reduced_dataset_data(clean_dataset)

        return response.handle_success(
            "Redução de dados realizada com sucesso!", clean_dataset_data
        )

    except Exception as e:
        return response.handle_internal_server_error_response(
            e, "Erro ao realizar a redução de dados!"
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
    file_name_with_extension = original_file_url.split("/")[-1]
    file_name = file_name_with_extension.split(".")[0]
    file_name = file_name.split("_")[0]

    reduced_file_name = f"{file_name}_reduced.csv"

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
