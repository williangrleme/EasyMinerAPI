from flask import Blueprint
from flask_login import login_required
from app.controllers.data_mining.preprocessing.data_cleaning_controller import (
    data_cleaning,
)
from app.controllers.data_mining.preprocessing.data_normalization_controller import (
    data_normalization,
)
from app.controllers.data_mining.preprocessing.data_reduction_controller import (
    data_reduction,
)

preprocessing_bp = Blueprint("preprocessing", __name__)

preprocessing_bp.route("/data-cleaning/<int:dataset_id>", methods=["POST"])(
    login_required(data_cleaning)
)
preprocessing_bp.route("/data-normalization/<int:dataset_id>", methods=["POST"])(
    login_required(data_normalization)
)
preprocessing_bp.route("/data-reduction/<int:dataset_id>", methods=["POST"])(
    login_required(data_reduction)
)
