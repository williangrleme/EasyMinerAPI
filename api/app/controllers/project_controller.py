import app.response_handlers as response
from app import db
from flask_login import current_user

from ..forms.project_form import ProjectFormCreate, ProjectFormUpdate
from ..models import Dataset, Project
from .dataset_controller import delete_dataset


def format_project_data(project, dataset_info=None):
    project_info = {
        "id": project.id,
        "name": project.name,
        "description": project.description,
    }

    if dataset_info is not None:
        project_info["datasets"] = dataset_info
    return project_info


def get_projects():
    projects = Project.query.filter_by(user_id=current_user.id).all()
    projects_list = [format_project_data(project) for project in projects]
    return response.handle_success(
        "Projetos recuperados com sucesso!",
        projects_list,
    )


def get_datasets_info(datasets):
    return [
        {
            "id": dataset.id,
            "name": dataset.name,
            "description": dataset.description,
            "size_file": dataset.size_file,
            "file_url": dataset.file_url,
        }
        for dataset in datasets
    ]


def get_project(project_id):
    project = Project.query.filter_by(id=project_id, user_id=current_user.id).first()
    if project is None:
        return response.handle_not_found_response(message="Projeto não encontrado!")

    datasets_info = get_datasets_info(project.datasets) if project.datasets else None
    project_data = format_project_data(project, datasets_info)

    return response.handle_success(
        "Projeto recuperado com sucesso!",
        project_data,
    )


def create_project():
    form = ProjectFormCreate()
    if not form.validate_on_submit():
        return response.handle_unprocessable_entity(form.errors)

    new_project = Project(
        name=form.name.data,
        description=form.description.data,
        user_id=current_user.id,
    )

    try:
        db.session.add(new_project)
        db.session.commit()
        project_data = format_project_data(new_project)
        return response.handle_success(
            "Projeto criado com sucesso!",
            project_data,
        )
    except Exception as e:
        db.session.rollback()
        response.log_error("Erro ao criar projeto", e)
        return response.handle_internal_server_error_response(
            error=e, message="Erro ao criar o projeto"
        )


def update_project(project_id):
    project = Project.query.get(project_id)
    if project is None or project.user_id != current_user.id:
        return response.handle_not_found_response(message="Projeto não encontrado!")

    form = ProjectFormUpdate(project_id=project_id)
    if not form.validate_on_submit():
        return response.handle_unprocessable_entity(form.errors)

    updated = False
    for field_name, field in form._fields.items():
        if field.data and getattr(project, field_name) != field.data:
            setattr(project, field_name, field.data)
            updated = True

    if updated:
        try:
            db.session.commit()
            project_data = format_project_data(project)
            return response.handle_success(
                "Projeto atualizado com sucesso!",
                project_data,
            )
        except Exception as e:
            db.session.rollback()
            return response.handle_internal_server_error_response(
                error=e, message="Erro ao atualizar o projeto"
            )

    return response.handle_success("Nenhuma alteração realizada no projeto.")


def delete_related_datasets(project_id):
    try:
        datasets = Dataset.query.filter_by(project_id=project_id).all()
        for dataset in datasets:
            delete_dataset(dataset.id)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        response.log_error("Erro ao deletar bases de dados relacionadas", e)
        return False


def delete_project(project_id):
    project = Project.query.get(project_id)

    if project is None or project.user_id != current_user.id:
        return response.handle_not_found_response("Projeto não encontrado!")

    project_data = format_project_data(project)
    try:
        if not delete_related_datasets(project_id):
            return response.handle_internal_server_error_response(
                message="Erro ao deletar bases de dados relacionadas ao projeto"
            )

        db.session.delete(project)
        db.session.commit()
        return response.handle_success(
            "Projeto deletado com sucesso!",
            project_data,
        )
    except Exception as e:
        db.session.rollback()
        return response.handle_internal_server_error_response(
            error=e, message="Erro ao deletar o projeto"
        )
