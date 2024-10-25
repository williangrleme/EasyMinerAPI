from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "invalid_email": "Por favor, insira um endereço de email válido.",
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
