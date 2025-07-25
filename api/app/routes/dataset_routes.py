from app.controllers.dataset_controller import (create_dataset, delete_dataset,
                                                get_dataset, get_datasets,
                                                update_dataset)
from flask import Blueprint
from flask_login import login_required

dataset_bp = Blueprint("datasets", __name__)

dataset_bp.route("/", methods=["GET"])(login_required(get_datasets))
dataset_bp.route("/<int:dataset_id>", methods=["GET"])(login_required(get_dataset))
dataset_bp.route("/create-dataset", methods=["POST"])(
    login_required(create_dataset)
)  # ISSO É UMA GAMBIARRA
dataset_bp.route("/<int:dataset_id>", methods=["PUT"])(login_required(update_dataset))
dataset_bp.route("/<int:dataset_id>", methods=["DELETE"])(
    login_required(delete_dataset)
)
