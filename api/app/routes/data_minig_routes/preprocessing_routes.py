from flask import Blueprint
from flask_login import login_required
from app.controllers.data_mining.preprocessing.data_cleaning_controller import (
    dataCleaning,
)

preprocessing_bp = Blueprint("preprocessing", __name__)

preprocessing_bp.route("/data-cleaning/<int:id>", methods=["POST"])(
    login_required(dataCleaning)
)
