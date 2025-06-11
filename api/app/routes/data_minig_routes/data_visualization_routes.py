from app.controllers.data_mining.data_visualization_controller import (
    frequency_distribution, mean_frequency_distribution, median, midpoint,
    mode, weighted_average, geometric_mean, harmonic_mean)
from flask import Blueprint
from flask_login import login_required

data_visualization_bp = Blueprint("data-visualization", __name__)

data_visualization_bp.route(
    "/frequency-distribution/<int:dataset_id>", methods=["POST"]
)(login_required(frequency_distribution))

data_visualization_bp.route("/mode/<int:dataset_id>", methods=["POST"])(
    login_required(mode)
)

data_visualization_bp.route("/midpoint/<int:dataset_id>", methods=["POST"])(
    login_required(midpoint)
)

data_visualization_bp.route("/median/<int:dataset_id>", methods=["POST"])(
    login_required(median)
)


data_visualization_bp.route("/weighted-average/<int:dataset_id>", methods=["POST"])(
    login_required(weighted_average)
)

data_visualization_bp.route(
    "/mean-frequency-distribution/<int:dataset_id>", methods=["POST"]
)(login_required(mean_frequency_distribution))

data_visualization_bp.route(
    "/geometric-mean/<int:dataset_id>", methods=["POST"]
)(login_required(geometric_mean))

data_visualization_bp.route(
    "/harmonic-mean/<int:dataset_id>", methods=["POST"]
)(login_required(harmonic_mean))


