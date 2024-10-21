from flask import jsonify
from flask_login import login_user, logout_user, current_user
from app.models import User
from app.forms.login_form import LoginForm


def login():
    form = LoginForm()
    if current_user.is_authenticated:
        logout_user()

    if not form.validate_on_submit():
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

    user = User.query.filter_by(email=form.email.data).first()
    if user is None or not user.check_password(form.password.data):
        return (
            jsonify(
                {
                    "message": "Credenciais inválidas!",
                    "success": False,
                    "data": None,
                }
            ),
            401,
        )

    login_user(user)
    return (
        jsonify(
            {
                "message": "Login realizado com sucesso!",
                "success": True,
                "data": None,
            }
        ),
        200,
    )


def logout():
    logout_user()
    return (
        jsonify(
            {
                "message": "Logout realizado com sucesso!",
                "success": True,
                "data": None,
            }
        ),
        200,
    )


def get_current_user():
    if current_user.is_authenticated:
        user_data = {
            "id": current_user.id,
            "name": current_user.name,
            "phone_number": current_user.phone_number,
            "email": current_user.email,
        }
        return (
            jsonify(
                {
                    "message": "Usuário atual recuperado com sucesso!",
                    "success": True,
                    "data": user_data,
                }
            ),
            200,
        )
    return (
        jsonify(
            {
                "message": "Não autorizado!",
                "success": False,
                "data": None,
            }
        ),
        403,
    )


def get_csrf_token():
    from flask_wtf.csrf import generate_csrf

    token = generate_csrf()
    return (
        jsonify(
            {
                "message": "Token CSRF gerado com sucesso!",
                "success": True,
                "data": {"csrf_token": token},
            }
        ),
        200,
    )
