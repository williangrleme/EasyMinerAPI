import hashlib
import boto3
from flask import jsonify, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError
from app import db
from app.models import Dataset
from app.forms.dataset_form import DatasetFormCreate, DatasetFormUpdate


class S3Service:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=current_app.config["S3_KEY"],
            aws_secret_access_key=current_app.config["S3_SECRET"],
        )
        self.bucket_name = current_app.config["S3_BUCKET"]

    def upload_file_to_s3(self, file, acl="public-read"):
        try:
            self.s3.upload_fileobj(
                file,
                self.bucket_name,
                file.filename,
                ExtraArgs={"ACL": acl, "ContentType": file.content_type},
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{file.filename}"
        except Exception as e:
            current_app.logger.error(f"Failed to upload to S3: {e}")
            return str(e)

    def delete_file_from_s3(self, file_url):
        s3_key = file_url.split("/")[-1]
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
        except NoCredentialsError:
            return False
        return True


def get_datasets():
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    datasets = Dataset.query.filter_by(user_id=current_user.id).all()
    datasets_list = [
        {
            "id": ds.id,
            "name": ds.name,
            "description": ds.description,
            "target": ds.target,
            "size_file": ds.size_file,
            "link_file": ds.link_file,
            "project_id": ds.project_id,
            "user_id": ds.user_id,
        }
        for ds in datasets
    ]
    return jsonify(datasets_list), 200


def get_dataset(id):
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    dataset_data = {
        "id": dataset.id,
        "name": dataset.name,
        "description": dataset.description,
        "target": dataset.target,
        "size_file": dataset.size_file,
        "link_file": dataset.link_file,
        "project_id": dataset.project_id,
        "user_id": dataset.user_id,
    }
    return jsonify(dataset_data), 200


def create_dataset():
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    form = DatasetFormCreate()
    if form.validate_on_submit():
        csv_file = form.csv_file.data
        size_file_with_unit = f"{round(csv_file.tell() / (1024 * 1024), 2)}MB"
        csv_file.seek(0)

        file_hash = hashlib.md5(
            f"{current_user.id}_{form.name.data}".encode("utf-8")
        ).hexdigest()
        csv_file.filename = f"{file_hash}.csv"

        s3_service = S3Service()
        link_file = s3_service.upload_file_to_s3(csv_file)

        new_dataset = Dataset(
            name=form.name.data,
            description=form.description.data,
            target=form.target.data,
            size_file=size_file_with_unit,
            project_id=form.project_id.data,
            user_id=current_user.id,
            link_file=link_file,
        )
        db.session.add(new_dataset)
        db.session.commit()
        return jsonify({"mensagem": "Base de dados criada com sucesso!"}), 201

    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def update_dataset(id):
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    form = DatasetFormUpdate()
    if form.validate_on_submit():
        s3_service = S3Service()

        if form.csv_file.data:
            csv_file = form.csv_file.data
            size_file_with_unit = f"{round(csv_file.tell() / (1024 * 1024), 2)}MB"
            csv_file.seek(0)

            file_hash = hashlib.md5(
                f"{current_user.id}_{form.name.data}".encode("utf-8")
            ).hexdigest()
            csv_file.filename = f"{file_hash}.csv"

            link_file = s3_service.upload_file_to_s3(csv_file)
            dataset.size_file = size_file_with_unit
            dataset.link_file = link_file

        dataset.name = form.name.data or dataset.name
        dataset.description = form.description.data or dataset.description
        dataset.target = form.target.data or dataset.target
        dataset.project_id = form.project_id.data or dataset.project_id

        db.session.commit()
        return jsonify({"mensagem": "Base de dados atualizada com sucesso!"}), 200

    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def delete_dataset(id):
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    if dataset.link_file:
        s3_service = S3Service()
        if not s3_service.delete_file_from_s3(dataset.link_file):
            return (
                jsonify({"mensagem": "Credenciais inválidas para acesso ao S3."}),
                403,
            )

    db.session.delete(dataset)
    db.session.commit()
    return jsonify({"mensagem": "Base de dados deletada com sucesso!"}), 200
