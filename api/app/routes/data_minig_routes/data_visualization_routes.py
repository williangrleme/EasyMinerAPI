from app.controllers.data_mining.data_visualization_controller import (
    association_measure, dispersion_measure, measure_central_tendency,
    shape_measure)
from flask import Blueprint
from flask_login import login_required

data_visualization_bp = Blueprint("data-visualization", __name__)

data_visualization_bp.route(
    "/measure-central-tendency/<int:dataset_id>", methods=["POST"]
)(login_required(measure_central_tendency))

data_visualization_bp.route("/dispersion-measure/<int:dataset_id>", methods=["POST"])(
    login_required(dispersion_measure)
)

data_visualization_bp.route("/shape-measure/<int:dataset_id>", methods=["POST"])(
    login_required(shape_measure)
)

data_visualization_bp.route("/association-measure/<int:dataset_id>", methods=["POST"])(
    login_required(association_measure)
)
