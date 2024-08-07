from flask import jsonify, request, current_app
from flask_login import current_user
from app.models import Dataset
from app import db
from app.forms.dataset_form import DatasetFormCreate, DatasetFormUpdate
import os
from flask import current_app
from werkzeug.utils import secure_filename
import hashlib


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
        # Obter o arquivo CSV
        csv_file = form.csv_file.data

        # Calcular o tamanho do arquivo em MB
        csv_file.seek(0, os.SEEK_END)  # Move o ponteiro para o final do arquivo
        size_file_bytes = csv_file.tell()  # Tamanho do arquivo em bytes
        size_file_mb = round(
            size_file_bytes / (1024 * 1024), 2
        )  # Converte para MB e arredonda
        csv_file.seek(0)  # Retorna o ponteiro para o início do arquivo

        # Formatar o tamanho com unidade "MB"
        size_file_with_unit = f"{size_file_mb}MB"

        # Gerar nome de arquivo único
        hash_input = f"{current_user.id}_{form.name.data}".encode("utf-8")
        file_hash = hashlib.md5(hash_input).hexdigest()
        filename = f"{file_hash}.csv"

        # Caminho completo do arquivo
        file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

        # Verificar se o arquivo já existe
        if os.path.exists(file_path):
            return (
                jsonify(
                    {
                        "mensagem": "O arquivo já existe. Reutilizando o arquivo existente."
                    }
                ),
                200,
            )

        # Salvar o arquivo
        csv_file.save(file_path)

        # Criar o novo dataset
        new_dataset = Dataset(
            name=form.name.data,
            description=form.description.data,
            target=form.target.data,
            size_file=size_file_with_unit,  # Armazenar o tamanho com unidade "MB"
            project_id=form.project_id.data,
            user_id=current_user.id,
            link_file=file_path,  # Armazenar o caminho do arquivo
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

    form = DatasetFormUpdate(dataset_id=id)
    if form.validate_on_submit():
        # Se um novo arquivo CSV for fornecido, processe-o
        if form.csv_file.data:
            # Excluir o arquivo atual, se existir
            if dataset.link_file and os.path.exists(dataset.link_file):
                os.remove(dataset.link_file)

            # Obter o novo arquivo CSV
            csv_file = form.csv_file.data

            # Calcular o tamanho do arquivo em MB
            csv_file.seek(0, os.SEEK_END)
            size_file_bytes = csv_file.tell()
            size_file_mb = round(size_file_bytes / (1024 * 1024), 2)
            csv_file.seek(0)

            # Formatar o tamanho com unidade "MB"
            size_file_with_unit = f"{size_file_mb}MB"

            # Gerar nome de arquivo único
            hash_input = f"{current_user.id}_{form.name.data}".encode("utf-8")
            file_hash = hashlib.md5(hash_input).hexdigest()
            filename = f"{file_hash}.csv"

            # Caminho completo do novo arquivo
            file_path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

            # Salvar o novo arquivo
            csv_file.save(file_path)

            # Atualizar campos relacionados ao arquivo
            dataset.size_file = size_file_with_unit
            dataset.link_file = file_path

        # Atualizar outros campos do dataset
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

    # Excluir o arquivo associado, se existir
    if dataset.link_file and os.path.exists(dataset.link_file):
        os.remove(dataset.link_file)

    db.session.delete(dataset)
    db.session.commit()
    return jsonify({"mensagem": "Base de dados deletada com sucesso!"}), 200
