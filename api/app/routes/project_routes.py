from flask import Blueprint
from flask_login import login_required
from api.app.controllers.project_controller import (
    get_projects,
    get_project,
    create_project,
    update_project,
    delete_project,
)

project_bp = Blueprint("projects", __name__)

project_bp.route("/", methods=["GET"])(get_projects)
project_bp.route("/<int:id>", methods=["GET"])(login_required(get_project))
project_bp.route("/", methods=["POST"])(create_project)
project_bp.route("/<int:id>", methods=["PUT"])(login_required(update_project))
project_bp.route("/<int:id>", methods=["DELETE"])(login_required(delete_project))
