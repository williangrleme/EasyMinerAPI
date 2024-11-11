from app.controllers.auth_controller import (
    get_csrf_token,
    get_current_user,
    login,
    logout,
)
from flask import Blueprint
from flask_login import login_required

auth_bp = Blueprint("auth", __name__)

auth_bp.route("/csrf-token", methods=["GET"])(get_csrf_token)
auth_bp.route("/login", methods=["POST"])(login)
auth_bp.route("/logout", methods=["POST"])(login_required(logout))
auth_bp.route("/me", methods=["GET"])(login_required(get_current_user))
