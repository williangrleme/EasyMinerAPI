from app import db
from app.forms.project_form import ProjectFormCreate, ProjectFormUpdate
from app.models import Project
from collections import OrderedDict
from flask import Response
from flask_login import current_user
import json


def create_response(message, success, data=None, status_code=200):
    response_data = OrderedDict(
        [
            ("message", message),
            ("success", success),
            ("data", data),
        ]
    )
    response_json = json.dumps(response_data)
    return Response(response_json, mimetype="application/json", status=status_code)


def get_projects():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    projects_list = [
        OrderedDict(
            [
                ("id", project.id),
                ("name", project.name),
                ("description", project.description),
            ]
        )
        for project in projects
    ]
    return create_response(
        "Projetos recuperados com sucesso!",
        True,
        projects_list,
        200,
    )


def get_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if project is None:
        return create_response(
            "Projeto não encontrado!",
            False,
            None,
            404,
        )

    project_data = OrderedDict(
        [
            ("id", project.id),
            ("name", project.name),
            ("description", project.description),
            (
                "datasets",
                [
                    OrderedDict(
                        [
                            ("id", dataset.id),
                            ("name", dataset.name),
                            ("description", dataset.description),
                            ("size_file", dataset.size_file),
                            ("file_url", dataset.file_url),
                        ]
                    )
                    for dataset in project.datasets
                ],
            ),
        ]
    )
    return create_response(
        "Projeto recuperado com sucesso!",
        True,
        project_data,
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
        project_data = OrderedDict(
            [
                ("id", new_project.id),
                ("name", new_project.name),
                ("description", new_project.description),
            ]
        )
        return create_response(
            "Projeto criado com sucesso!",
            True,
            project_data,
            201,
        )
    return create_response(
        "Dados inválidos!",
        False,
        form.errors,
        422,
    )


def update_project(project_id):
    project = Project.query.get(project_id)
    if project is None or project.user_id != current_user.id:
        return create_response(
            "Projeto não encontrado!",
            False,
            None,
            404,
        )

    form = ProjectFormUpdate(project_id=project_id)
    if form.validate_on_submit():
        updated = False
        for field_name, field in form._fields.items():
            if field.data and getattr(project, field_name) != field.data:
                setattr(project, field_name, field.data)
                updated = True
        if updated:
            db.session.commit()
        project_data = OrderedDict(
            [
                ("id", project.id),
                ("name", project.name),
                ("description", project.description),
            ]
        )
        return create_response(
            "Projeto atualizado com sucesso!",
            True,
            project_data,
            200,
        )

    return create_response(
        "Dados inválidos!",
        False,
        form.errors,
        422,
    )


def delete_project(project_id):
    project = Project.query.get(project_id)
    if project and project.user_id == current_user.id:
        project_data = OrderedDict(
            [
                ("id", project.id),
                ("name", project.name),
                ("description", project.description),
            ]
        )
        db.session.delete(project)
        db.session.commit()
        return create_response(
            "Projeto deletado com sucesso!",
            True,
            project_data,
            200,
        )
    return create_response(
        "Projeto não encontrado!",
        False,
        None,
        404,
    )
