from flask import Blueprint
from flask_login import login_required
from app.controllers.dataset_controller import (
    get_datasets,
    get_dataset,
    create_dataset,
    update_dataset,
    delete_dataset,
)

dataset_bp = Blueprint("datasets", __name__)

dataset_bp.route("/", methods=["GET"])(get_datasets)
dataset_bp.route("/<int:id>", methods=["GET"])(login_required(get_dataset))
dataset_bp.route("/", methods=["POST"])(create_dataset)
dataset_bp.route("/<int:id>", methods=["PUT"])(login_required(update_dataset))
dataset_bp.route("/<int:id>", methods=["DELETE"])(login_required(delete_dataset))
