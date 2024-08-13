from app.models import Dataset
from flask_login import current_user
from flask import jsonify, current_app
from app.forms.data_mining_forms.preprocessing.data_cleaning_forms import (
    DataCleaningForm,
)


def dataCleaning(id):
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    dataset = Dataset.query.get(id)
    if dataset is None or dataset.user_id != current_user.id:
        return jsonify({"mensagem": "Base de dados não encontrada!"}), 404

    form = DataCleaningForm(file_url=dataset.file_url)

    if form.validate_on_submit():
        target = form.target.data
        features = form.features.data
        methods = form.methods.data
        return jsonify({"mensagem": "Deu bom!"}), 201
    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422
