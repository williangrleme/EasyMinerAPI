from app.models import User
from flask_wtf import FlaskForm
from wtforms import PasswordField, StringField
from wtforms.validators import (DataRequired, Email, Length, Optional,
                                ValidationError)


class UserFormBase(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "size_length": "Tamanho deve estar entre {} e {}.",
        "phone_number_exists": "Número de telefone já cadastrado.",
        "email_exists": "E-mail já cadastrado.",
        "invalid_email": "Endereço de email inválido.",
    }

    @staticmethod
    def size_length_message(min_length, max_length):
        return f"O tamanho deve estar entre {min_length} e {max_length} caracteres."

    name = StringField(
        "Nome",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
            Length(min=10, max=150, message=size_length_message(10, 150)),
        ],
    )

    phone_number = StringField(
        "Número de telefone",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
            Length(min=11, max=20, message=size_length_message(11, 20)),
        ],
    )

    email = StringField(
        "E-mail",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
            Length(min=6, max=200, message=size_length_message(6, 200)),
            Email(message=ERROR_MESSAGES["invalid_email"]),
        ],
    )

    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
            Length(min=8, max=30, message=size_length_message(8, 30)),
        ],
    )

    def validate_phone_number(self, field):
        if User.query.filter_by(phone_number=field.data).first():
            raise ValidationError(self.ERROR_MESSAGES["phone_number_exists"])

    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError(self.ERROR_MESSAGES["email_exists"])


class UserFormCreate(UserFormBase):
    pass


class UserFormUpdate(UserFormBase):
    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = user_id

    def validate_phone_number(self, field):
        if field.data:
            if User.query.filter(
                User.phone_number == field.data, User.id != self.user_id
            ).first():
                raise ValidationError(self.ERROR_MESSAGES["phone_number_exists"])

    def validate_email(self, field):
        if field.data:
            if User.query.filter(
                User.email == field.data, User.id != self.user_id
            ).first():
                raise ValidationError(self.ERROR_MESSAGES["email_exists"])

    name = StringField(
        "Nome",
        validators=[
            Optional(),
            Length(min=10, max=150, message=UserFormBase.size_length_message(10, 150)),
        ],
    )

    phone_number = StringField(
        "Número de telefone",
        validators=[
            Optional(),
            Length(min=11, max=20, message=UserFormBase.size_length_message(11, 20)),
        ],
    )

    email = StringField(
        "E-mail",
        validators=[
            Optional(),
            Length(min=6, max=200, message=UserFormBase.size_length_message(6, 200)),
            Email(message=UserFormBase.ERROR_MESSAGES["invalid_email"]),
        ],
    )
    password = PasswordField(
        "Senha",
        validators=[
            Optional(),
            Length(min=8, max=30, message=UserFormBase.size_length_message(8, 30)),
        ],
    )
