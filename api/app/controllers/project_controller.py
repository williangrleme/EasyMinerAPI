from flask import jsonify
from flask_login import current_user
from app.models import Project
from app import db
from app.forms.project_form import ProjectFormCreate, ProjectFormUpdate


def get_projects():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    projects_list = [
        {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "datasets": [
                {
                    "id": dataset.id,
                    "name": dataset.name,
                    "description": dataset.description,
                    "size_file": dataset.size_file,
                    "file_url": dataset.file_url,
                }
                for dataset in project.datasets
            ],
        }
        for project in projects
    ]
    return (
        jsonify(
            {
                "message": "Projetos recuperados com sucesso!",
                "success": True,
                "data": projects_list,
            }
        ),
        200,
    )


def get_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if project is None:
        return (
            jsonify(
                {
                    "message": "Projeto não encontrado!",
                    "success": False,
                    "data": None,
                }
            ),
            404,
        )

    project_data = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
        "datasets": [
            {
                "id": dataset.id,
                "name": dataset.name,
                "description": dataset.description,
                "size_file": dataset.size_file,
                "file_url": dataset.file_url,
            }
            for dataset in project.datasets
        ],
    }
    return (
        jsonify(
            {
                "message": "Projeto recuperado com sucesso!",
                "success": True,
                "data": project_data,
            }
        ),
        200,
    )


def create_project():
    form = ProjectFormCreate()
    if form.validate_on_submit():
        new_project = Project(
            name=form.name.data,
            description=form.description.data,
            user_id=current_user.id,
        )
        db.session.add(new_project)
        db.session.commit()
        project_data = {
            "id": new_project.id,
            "name": new_project.name,
            "description": new_project.description,
        }
        return (
            jsonify(
                {
                    "message": "Projeto criado com sucesso!",
                    "success": True,
                    "data": project_data,
                }
            ),
            201,
        )
    return (
        jsonify(
            {
                "message": "Dados inválidos!",
                "success": False,
                "data": form.errors,
            }
        ),
        422,
    )


def update_project(id):
    project = Project.query.get(id)
    if project is None or project.user_id != current_user.id:
        return (
            jsonify(
                {
                    "message": "Projeto não encontrado!",
                    "success": False,
                    "data": None,
                }
            ),
            404,
        )

    form = ProjectFormUpdate(project_id=id)
    if form.validate_on_submit():
        updated = False
        for field_name, field in form._fields.items():
            if field.data and getattr(project, field_name) != field.data:
                setattr(project, field_name, field.data)
                updated = True
        if updated:
            db.session.commit()
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
        }
        return (
            jsonify(
                {
                    "message": "Projeto atualizado com sucesso!",
                    "success": True,
                    "data": project_data,
                }
            ),
            200,
        )

    return (
        jsonify(
            {
                "message": "Dados inválidos!",
                "success": False,
                "data": form.errors,
            }
        ),
        422,
    )


def delete_project(id):
    project = Project.query.get(id)
    if project and project.user_id == current_user.id:
        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
        }
        db.session.delete(project)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Projeto deletado com sucesso!",
                    "success": True,
                    "data": project_data,
                }
            ),
            200,
        )
    return (
        jsonify(
            {
                "message": "Projeto não encontrado!",
                "success": False,
                "data": None,
            }
        ),
        404,
    )
