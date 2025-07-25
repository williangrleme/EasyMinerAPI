from app.controllers.data_mining.classification_controller import \
    classification_algorithm
from flask import Blueprint
from flask_login import login_required

classification_bp = Blueprint("classification", __name__)

classification_bp.route("/<int:dataset_id>", methods=["POST"])(
    login_required(classification_algorithm)
)
