from app.controllers.data_mining.data_visualization_controller import \
    frequency_distribution
from flask import Blueprint
from flask_login import login_required

data_visualization_bp = Blueprint("data_visualization", __name__)

data_visualization_bp.route(
    "/frequency_distribution/<int:dataset_id>", methods=["POST"]
)(login_required(frequency_distribution))
