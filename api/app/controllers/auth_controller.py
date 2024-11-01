from app.forms.login_form import LoginForm
from app.models import User
from collections import OrderedDict
from flask import Response
from flask_login import current_user, login_user, logout_user
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


def login():
    form = LoginForm()
    if current_user.is_authenticated:
        logout_user()

    if not form.validate_on_submit():
        return create_response(
            "Dados inválidos!",
            False,
            form.errors,
            422,
        )

    user = User.query.filter_by(email=form.email.data).first()
    if user is None or not user.check_password(form.password.data):
        return create_response(
            "Credenciais inválidas!",
            False,
            None,
            401,
        )

    login_user(user)
    return create_response(
        "Login realizado com sucesso!",
        True,
        None,
        200,
    )


def logout():
    logout_user()
    return create_response(
        "Logout realizado com sucesso!",
        True,
        None,
        200,
    )


def get_current_user():
    if current_user.is_authenticated:
        user_data = OrderedDict(
            [
                ("id", current_user.id),
                ("name", current_user.name),
                ("phone_number", current_user.phone_number),
                ("email", current_user.email),
            ]
        )
        return create_response(
            "Usuário atual recuperado com sucesso!",
            True,
            user_data,
            200,
        )
    return create_response(
        "Não autorizado!",
        False,
        None,
        403,
    )


def get_csrf_token():
    from flask_wtf.csrf import generate_csrf

    token = generate_csrf()
    return create_response(
        "Token CSRF gerado com sucesso!",
        True,
        {"csrf_token": token},
        200,
    )
