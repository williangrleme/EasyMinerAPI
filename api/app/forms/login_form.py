from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email


class LoginForm(FlaskForm):
    email = StringField(
        "Email", validators=[DataRequired(message="O campo é obrigatório."), Email()]
    )
    password = PasswordField(
        "Password", validators=[DataRequired(message="O campo é obrigatório.")]
    )
