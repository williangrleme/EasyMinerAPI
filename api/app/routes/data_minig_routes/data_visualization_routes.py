from app.controllers.data_mining.data_visualization_controller import (data_visualization)
from flask import Blueprint
from flask_login import login_required

data_visualization_bp = Blueprint("data-visualization", __name__)

data_visualization_bp.route(
    "/visualize/<int:dataset_id>", methods=["POST"]
)(login_required(data_visualization))
