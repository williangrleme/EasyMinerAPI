from flask import jsonify
from flask_login import current_user
from app.models import Project
from app import db
from app.forms.project_form import ProjectFormCreate, ProjectFormUpdate


def get_projects():
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    projects = Project.query.filter_by(user_id=current_user.id).all()
    projects_list = [
        {
            "id": project.id,
            "name": project.name,
            "description": project.description,
        }
        for project in projects
    ]
    return jsonify(projects_list), 200


def get_project(id):
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    project = Project.query.get(id)
    if project is None or project.user_id != current_user.id:
        return jsonify({"mensagem": "Projeto não encontrado!"}), 404

    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
    }
    return jsonify(project_data), 200


def create_project():
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    form = ProjectFormCreate()
    if form.validate_on_submit():
        new_project = Project(
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id,
        )
        db.session.add(new_project)
        db.session.commit()
        return jsonify({"mensagem": "Projeto criado com sucesso!"}), 201
    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def update_project(id):
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    project = Project.query.get(id)
    if project is None or project.user_id != current_user.id:
        return jsonify({"mensagem": "Projeto não encontrado!"}), 404

    form = ProjectFormUpdate(project_id=id)
    if form.validate_on_submit():
        for field_name, field in form._fields.items():
            if field.data:
                setattr(project, field_name, field.data)
        db.session.commit()
        return jsonify({"mensagem": "Projeto atualizado com sucesso!"}), 200

    return jsonify({"mensagem": "Dados inválidos!", "erros": form.errors}), 422


def delete_project(id):
    if not current_user.is_authenticated:
        return jsonify({"mensagem": "Não autorizado!"}), 403

    project = Project.query.get(id)
    if project is None or project.user_id != current_user.id:
        return jsonify({"mensagem": "Projeto não encontrado!"}), 404

    db.session.delete(project)
    db.session.commit()
    return jsonify({"mensagem": "Projeto deletado com sucesso!"}), 200
