from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.data_mining.cleaning import DataCleaningSchema
from app.schemas.data_mining.normalization import DataNormalizationSchema

preprocessing_bp = Blueprint("preprocessing", __name__)


@preprocessing_bp.post("/data-cleaning/<int:dataset_id>")
@login_required
@handle_errors
def data_cleaning(dataset_id):
    data = DataCleaningSchema.model_validate(request.get_json(silent=True) or {})
    clean = current_app.services["cleaning"].clean(dataset_id, data, current_user.id)
    payload = {"clean_dataset": {"id": clean.id, "size_file": clean.size_file, "file_url": clean.file_url}}
    body, status = success_payload("Limpeza de dados realizada com sucesso!", payload)
    return jsonify(body), status


@preprocessing_bp.post("/data-normalization/<int:dataset_id>")
@login_required
@handle_errors
def data_normalization(dataset_id):
    data = DataNormalizationSchema.model_validate(request.get_json(silent=True) or {})
    clean = current_app.services["normalization"].normalize(dataset_id, data, current_user.id)
    payload = {"normalized_dataset": {"id": clean.id, "size_file": clean.size_file, "file_url": clean.file_url}}
    body, status = success_payload("Normalização de dados realizada com sucesso!", payload)
    return jsonify(body), status
