from app import db
from app.forms.user_form import UserFormCreate, UserFormUpdate
from app.models import User
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
        user_data = OrderedDict(
            [
                ("id", new_user.id),
                ("name", new_user.name),
                ("phone_number", new_user.phone_number),
                ("email", new_user.email),
            ]
        )
        return create_response(
            "Usuário criado com sucesso!",
            True,
            user_data,
            201,
        )
    return create_response(
        "Dados inválidos!",
        False,
        form.errors,
        422,
    )


def update_user():
    user = User.query.get(current_user.id)
    if user is None:
        return create_response(
            "Usuário não encontrado!",
            False,
            None,
            404,
        )

    form = UserFormUpdate(user_id=current_user.id, obj=user)
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
        user_data = OrderedDict(
            [
                ("id", user.id),
                ("name", user.name),
                ("phone_number", user.phone_number),
                ("email", user.email),
            ]
        )
        return create_response(
            "Usuário atualizado com sucesso!",
            True,
            user_data,
            200,
        )

    return create_response(
        "Dados inválidos!",
        False,
        form.errors,
        422,
    )


def delete_user():
    user = User.query.get(current_user.id)
    user_data = OrderedDict(
        [
            ("id", user.id),
            ("name", user.name),
            ("phone_number", user.phone_number),
            ("email", user.email),
        ]
    )
    db.session.delete(user)
    db.session.commit()
    return create_response(
        "Usuário deletado com sucesso!",
        True,
        user_data,
        200,
    )
