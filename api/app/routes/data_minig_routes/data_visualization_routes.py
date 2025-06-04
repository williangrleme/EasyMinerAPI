from app.controllers.data_mining.data_visualization_controller import (
    frequency_distribution, mode)
from flask import Blueprint
from flask_login import login_required

data_visualization_bp = Blueprint("data-visualization", __name__)

data_visualization_bp.route(
    "/frequency-distribution/<int:dataset_id>", methods=["POST"]
)(login_required(frequency_distribution))

data_visualization_bp.route("/mode/<int:dataset_id>", methods=["POST"])(
    login_required(mode)
)
