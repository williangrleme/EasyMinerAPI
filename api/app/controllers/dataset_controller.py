from flask import jsonify, request
from flask_login import current_user
from app.models import Dataset
from app import db
from app.forms.dataset_form import DatasetFormCreate, DatasetFormUpdate


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
        new_dataset = Dataset(
            name=form.name.data,
            description=form.description.data,
            target=form.target.data,
            size_file=form.size_file.data,
            project_id=form.project_id.data,
            user_id=current_user.id,
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
        for field_name, field in form._fields.items():
            if field.data:
                setattr(dataset, field_name, field.data)
        db.session.commit()
        return jsonify({"mensagem": "Base de dados atualizada com sucesso!"}), 200

    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def delete_dataset(id):
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    db.session.delete(dataset)
    db.session.commit()
    return jsonify({"mensagem": "Base de dados deletada com sucesso!"}), 200
