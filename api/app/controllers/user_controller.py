from flask import jsonify, current_app
from flask_login import current_user
from app.models import User
from app import db
from app.forms.user_form import UserFormCreate, UserFormUpdate


def create_user():
    form = UserFormCreate()
    if form.validate_on_submit():
        new_user = User(
            name=form.name.data,
            phone_number=form.phone_number.data,
            email=form.email.data,
        )
        new_user.set_password(form.password.data)
        db.session.add(new_user)
        db.session.commit()
        user_data = {
            "id": new_user.id,
            "name": new_user.name,
            "phone_number": new_user.phone_number,
            "email": new_user.email,
        }
        return (
            jsonify(
                {
                    "message": "Usuário criado com sucesso!",
                    "success": True,
                    "data": user_data,
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


def update_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return (
            jsonify(
                {
                    "message": "Usuário não encontrado!",
                    "success": False,
                    "data": None,
                }
            ),
            404,
        )

    form = UserFormUpdate(user_id=user_id, obj=user)
    if form.validate_on_submit():
        updated = False
        for field_name, field in form._fields.items():
            if field.data and getattr(user, field_name) != field.data:
                setattr(user, field_name, field.data)
                updated = True
        if form.password.data and not user.check_password(form.password.data):
            user.set_password(form.password.data)
            updated = True
        if updated:
            db.session.commit()
        user_data = {
            "id": user.id,
            "name": user.name,
            "phone_number": user.phone_number,
            "email": user.email,
        }
        return (
            jsonify(
                {
                    "message": "Usuário atualizado com sucesso!",
                    "success": True,
                    "data": user_data,
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


def delete_user(user_id):
    user = User.query.get(user_id)
    if user:
        user_data = {
            "id": user.id,
            "name": user.name,
            "phone_number": user.phone_number,
            "email": user.email,
        }
        db.session.delete(user)
        db.session.commit()
        return (
            jsonify(
                {
                    "message": "Usuário deletado com sucesso!",
                    "success": True,
                    "data": user_data,
                }
            ),
            200,
        )
    return (
        jsonify(
            {
                "message": "Usuário não encontrado!",
                "success": False,
                "data": None,
            }
        ),
        404,
    )
