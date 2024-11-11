from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "invalid_email": "Endereço de email inválido.",
    }

    email = StringField(
        "Email",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
            Email(message=ERROR_MESSAGES["invalid_email"]),
        ],
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
        ],
    )
