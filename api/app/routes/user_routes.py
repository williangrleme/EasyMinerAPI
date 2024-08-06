from flask import Blueprint
from flask_login import login_required
from app.controllers.user_controller import (
    get_users,
    get_user,
    create_user,
    update_user,
    delete_user,
)

user_bp = Blueprint("users", __name__)

user_bp.route("/", methods=["GET"])(get_users)
user_bp.route("/<int:id>", methods=["GET"])(login_required(get_user))
user_bp.route("/", methods=["POST"])(create_user)
user_bp.route("/<int:id>", methods=["PUT"])(login_required(update_user))
user_bp.route("/<int:id>", methods=["DELETE"])(login_required(delete_user))
