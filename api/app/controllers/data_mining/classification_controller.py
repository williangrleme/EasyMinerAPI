from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.data_mining.classification import ClassificationSchema

classification_bp = Blueprint("classification", __name__)


@classification_bp.post("/<int:dataset_id>")
@login_required
@handle_errors
def classify(dataset_id):
    data = ClassificationSchema.model_validate(request.get_json(silent=True) or {})
    results = current_app.services["classification"].classify(dataset_id, data, current_user.id)
    body, status = success_payload(
        f"Algoritmo de classificação {data.classification_method.upper()} executado com sucesso!", results
    )
    return jsonify(body), status
