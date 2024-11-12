import app.response_handlers as response
from flask_login import current_user, login_user, logout_user

from ..forms.login_form import LoginForm
from ..models.user import User


def format_user_data(user):
    return {
        "id": user.id,
        "name": user.name,
        "phone_number": user.phone_number,
        "email": user.email,
    }


def validate_user_credentials(email, password):
    user = User.query.filter_by(email=email).first()
    if user and user.check_password(password):
        return user
    return None


def login():
    if current_user.is_authenticated:
        logout_user()

    form = LoginForm()
    if not form.validate_on_submit():
        return response.handle_unprocessable_entity(form.errors)

    user = validate_user_credentials(form.email.data, form.password.data)

    if not user:
        return response.handle_not_authorized_response("Credenciais inválidas!")

    login_user(user)

    return response.handle_success(
        "Login realizado com sucesso!",
        format_user_data(user),
    )


def logout():
    logout_user()
    return response.handle_success(
        "Logout realizado com sucesso!",
    )


def get_current_user():
    if current_user.is_authenticated:
        user_data = format_user_data(current_user)
        return response.handle_success(
            "Usuário atual recuperado com sucesso!",
            user_data,
        )


def get_csrf_token():
    from flask_wtf.csrf import generate_csrf

    token = generate_csrf()
    return response.create_response(
        "Token CSRF gerado com sucesso!",
        True,
        {"csrf_token": token},
        200,
    )
