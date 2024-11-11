from app.controllers.user_controller import create_user, delete_user, update_user
from flask import Blueprint
from flask_login import login_required

user_bp = Blueprint("users", __name__)

user_bp.route("/", methods=["POST"])(create_user)
user_bp.route("/", methods=["PUT"])(login_required(update_user))
user_bp.route("/", methods=["DELETE"])(login_required(delete_user))
