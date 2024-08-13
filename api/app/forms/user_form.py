from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length, ValidationError, Optional

from app.models import User


class UserFormCreate(FlaskForm):
    def validate_phone_number(self, field):
        if User.query.filter_by(phone_number=field.data).first():
            raise ValidationError("Phone number already registered.")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered.")

    name = StringField(
        "Name",
        validators=[
            DataRequired(message="O campo é obrigatório."),
            Length(min=10, max=150),
        ],
    )
    phone_number = StringField(
        "Phone number",
        validators=[
            DataRequired(message="O campo é obrigatório."),
            Length(min=11, max=20),
        ],
    )
    email = StringField(
        "Email",
        validators=[
            DataRequired(message="O campo é obrigatório."),
            Length(min=6, max=200),
            Email(),
        ],
    )
    password = PasswordField(
        "Password",
        validators=[
            DataRequired(message="O campo é obrigatório."),
            Length(min=8, max=30),
        ],
    )


class UserFormUpdate(FlaskForm):
    def __init__(self, user_id, *args, **kwargs):
        super(UserFormUpdate, self).__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_phone_number(self, field):
        if User.query.filter(
            User.phone_number == field.data, User.id != self.user_id
        ).first():
            raise ValidationError("Phone number already registered.")

    def validate_email(self, field):
        if User.query.filter(User.email == field.data, User.id != self.user_id).first():
            raise ValidationError("Email already registered.")

    name = StringField(
        "Name",
        validators=[
            Length(min=10, max=150),
        ],
    )
    phone_number = StringField(
        "Phone number",
        validators=[
            Length(min=11, max=20),
        ],
    )
    email = StringField("Email", validators=[Length(min=6, max=200), Email()])
    password = PasswordField(
        "Password",
        validators=[
            Length(min=8, max=30),
            Optional(),
        ],
    )
