import app.response_handlers as response
from app import db
from app.controllers.dataset_controller import delete_dataset
from app.controllers.project_controller import delete_project
from app.forms.user_form import UserFormCreate, UserFormUpdate
from app.models import CleanDataset, Dataset, Project, User
from flask_login import current_user


def format_user_data(user):
    return {
        "id": user.id,
        "name": user.name,
        "phone_number": user.phone_number,
        "email": user.email,
    }


def create_user():
    form = UserFormCreate()
    if not form.validate_on_submit():
        return response.handle_unprocessable_entity(form.errors)

    new_user = User(
        name=form.name.data,
        phone_number=form.phone_number.data,
        email=form.email.data,
    )
    new_user.set_password(form.password.data)

    try:
        db.session.add(new_user)
        db.session.commit()
        user_data = format_user_data(new_user)
        return response.handle_success(
            "Usuário criado com sucesso!",
            user_data,
        )
    except Exception as e:
        db.session.rollback()
        return response.handle_internal_server_error_response(
            error=e, message="Falha ao criar o usuário"
        )


def update_user():
    user = User.query.get(current_user.id)
    if not user:
        return response.handle_not_found_response(message="Usuário não encontrado!")

    form = UserFormUpdate(user_id=current_user.id, obj=user)
    if not form.validate_on_submit():
        return response.handle_unprocessable_entity(form.errors)

    updated = False

    if form.name.data and user.name != form.name.data:
        user.name = form.name.data
        updated = True

    if form.phone_number.data and user.phone_number != form.phone_number.data:
        user.phone_number = form.phone_number.data
        updated = True

    if form.email.data and user.email != form.email.data:
        user.email = form.email.data
        updated = True

    if form.password.data:
        user.set_password(form.password.data)
        updated = True

    if updated:
        try:
            db.session.commit()
            user_data = format_user_data(user)
            return response.handle_success(
                "Usuário atualizado com sucesso!",
                user_data,
            )
        except Exception as e:
            db.session.rollback()
            return response.handle_internal_server_error_response(
                error=e, message="Erro ao atualizar o usuário"
            )


def delete_user():
    user = User.query.get(current_user.id)
    if not user:
        return response.handle_not_found_response(message="Usuário não encontrado!")

    try:
        delete_user_related_data(current_user.id)
        user_data = format_user_data(user)
        db.session.delete(user)
        db.session.commit()
        return response.handle_success(
            "Usuário deletado com sucesso!",
            user_data,
        )
    except Exception as e:
        db.session.rollback()
        return response.handle_internal_server_error_response(
            error=e, message="Erro ao deletar o usuário!"
        )


def delete_user_related_data(user_id):
    try:
        projects = Project.query.filter_by(user_id=user_id).all()
        datasets = Dataset.query.filter_by(user_id=user_id).all()

        for project in projects:
            delete_project(project.id)
        for dataset in datasets:
            delete_dataset(dataset.id)

        CleanDataset.query.filter_by(user_id=user_id).delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return response.handle_internal_server_error_response(
            error=e, message="Erro ao deletar dados relacionados ao usuário!"
        )
