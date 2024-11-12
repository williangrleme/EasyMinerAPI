from app.controllers.project_controller import (create_project, delete_project,
                                                get_project, get_projects,
                                                update_project)
from flask import Blueprint
from flask_login import login_required

project_bp = Blueprint("projects", __name__)

project_bp.route("/", methods=["GET"])(login_required(get_projects))
project_bp.route("/<int:project_id>", methods=["GET"])(login_required(get_project))
project_bp.route("/", methods=["POST"])(login_required(create_project))
project_bp.route("/<int:project_id>", methods=["PUT"])(login_required(update_project))
project_bp.route("/<int:project_id>", methods=["DELETE"])(
    login_required(delete_project)
)
