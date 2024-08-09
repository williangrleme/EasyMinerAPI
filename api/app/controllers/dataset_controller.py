import os
import hashlib
import boto3
from flask import jsonify, request, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from botocore.exceptions import NoCredentialsError
from app import db
from app.models import Dataset
from app.forms.dataset_form import DatasetFormCreate, DatasetFormUpdate


class S3Service:
    def __init__(self):
        # Inicializa o cliente S3 com as credenciais da aplicação
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=current_app.config["S3_KEY"],
            aws_secret_access_key=current_app.config["S3_SECRET"],
        )
        # Nome do bucket S3, retirado da configuração da aplicação
        self.bucket_name = current_app.config["S3_BUCKET"]

    def upload_file_to_s3(self, file, acl="public-read"):
        """
        Faz o upload de um arquivo para o bucket S3.

        :param file: Arquivo a ser enviado
        :param acl: Configuração de controle de acesso do arquivo (padrão: public-read)
        :return: URL do arquivo no S3 ou mensagem de erro
        """
        try:
            self.s3.upload_fileobj(
                file,
                self.bucket_name,
                file.filename,
                ExtraArgs={"ACL": acl, "ContentType": file.content_type},
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{file.filename}"
        except Exception as e:
            # Loga o erro em caso de falha no upload
            current_app.logger.error(f"falha ao realizar upload para o S3: {e}")
            return str(e)

    def delete_file_from_s3(self, file_url):
        """
        Deleta um arquivo do bucket S3.

        :param file_url: URL completa do arquivo a ser deletado
        :return: True se o arquivo foi deletado com sucesso, False caso contrário
        """
        s3_key = file_url.split("/")[-1]  # Extrai a chave do arquivo a partir da URL
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
        except NoCredentialsError:
            # Retorna False se houver erro de credenciais
            return False
        return True


def get_datasets():
    """
    Retorna a lista de datasets do usuário autenticado.

    :return: JSON com a lista de datasets ou mensagem de erro
    """
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Busca todos os datasets associados ao usuário atual
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
    """
    Retorna os detalhes de um dataset específico.

    :param id: ID do dataset
    :return: JSON com os dados do dataset ou mensagem de erro
    """
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    # Busca o dataset pelo ID e valida se pertence ao usuário atual
    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    # Retorna os dados do dataset encontrado
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
    """
    Cria um novo dataset para o usuário autenticado.

    :return: JSON com mensagem de sucesso ou erro
    """
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    form = DatasetFormCreate()
    if form.validate_on_submit():
        csv_file = form.csv_file.data

        # Calcula o tamanho do arquivo em MB
        size_file_with_unit = f"{round(csv_file.tell() / (1024 * 1024), 2)}MB"
        csv_file.seek(0)  # Reseta o ponteiro do arquivo para o início

        # Gera um nome de arquivo único usando o ID do usuário e o nome do dataset
        file_hash = hashlib.md5(
            f"{current_user.id}_{form.name.data}".encode("utf-8")
        ).hexdigest()
        csv_file.filename = f"{file_hash}.csv"

        # Faz o upload do arquivo para o S3
        s3_service = S3Service()
        link_file = s3_service.upload_file_to_s3(csv_file)

        # Cria uma nova entrada de dataset no banco de dados
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

    # Retorna erros de validação, se houver
    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def update_dataset(id):
    """
    Atualiza um dataset existente.

    :param id: ID do dataset a ser atualizado
    :return: JSON com mensagem de sucesso ou erro
    """
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

            # Calcula o tamanho do arquivo em MB
            size_file_with_unit = f"{round(csv_file.tell() / (1024 * 1024), 2)}MB"
            csv_file.seek(0)  # Reseta o ponteiro do arquivo para o início

            # Gera um nome de arquivo único usando o ID do usuário e o nome do dataset
            file_hash = hashlib.md5(
                f"{current_user.id}_{form.name.data}".encode("utf-8")
            ).hexdigest()
            csv_file.filename = f"{file_hash}.csv"

            # Faz o upload do arquivo para o S3
            link_file = s3_service.upload_file_to_s3(csv_file)
            dataset.size_file = size_file_with_unit
            dataset.link_file = link_file

        # Atualiza os campos do dataset com os dados do formulário ou mantém os antigos
        dataset.name = form.name.data or dataset.name
        dataset.description = form.description.data or dataset.description
        dataset.target = form.target.data or dataset.target
        dataset.project_id = form.project_id.data or dataset.project_id

        db.session.commit()
        return jsonify({"mensagem": "Base de dados atualizada com sucesso!"}), 200

    # Retorna erros de validação, se houver
    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def delete_dataset(id):
    """
    Deleta um dataset existente.

    :param id: ID do dataset a ser deletado
    :return: JSON com mensagem de sucesso ou erro
    """
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    if dataset.link_file:
        # Deleta o arquivo associado no S3 antes de remover o dataset do banco de dados
        s3_service = S3Service()
        if not s3_service.delete_file_from_s3(dataset.link_file):
            return (
                jsonify({"mensagem": "Credenciais inválidas para acesso ao S3."}),
                403,
            )

    # Remove o dataset do banco de dados
    db.session.delete(dataset)
    db.session.commit()
    return jsonify({"mensagem": "Base de dados deletada com sucesso!"}), 200
