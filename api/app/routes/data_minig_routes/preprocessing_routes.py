from flask import Blueprint
from flask_login import login_required
from app.controllers.data_mining.preprocessing.data_cleaning_controller import (
    dataCleaning,
)
from app.controllers.data_mining.preprocessing.data_normalization_controller import (
    dataNormalization,
)

preprocessing_bp = Blueprint("preprocessing", __name__)

preprocessing_bp.route("/data-cleaning/<int:id>", methods=["POST"])(
    login_required(dataCleaning)
)
preprocessing_bp.route("/data-normalization/<int:id>", methods=["POST"])(
    login_required(dataNormalization)
)
