from app.models import Project
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Optional, ValidationError


class BaseProjectForm(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "name_exists": "O nome do projeto já existe.",
        "size_length": "Tamanho deve estar entre {} e {}.",
    }

    @staticmethod
    def size_length_message(min_length, max_length):
        return f"O tamanho deve estar entre {min_length} e {max_length} caracteres."

    name = StringField(
        "Name",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
            Length(min=2, max=100, message=size_length_message(10, 150)),
        ],
    )

    description = StringField(
        "Description",
        validators=[
            Optional(),
            Length(min=10, max=2000, message=size_length_message(10, 150)),
        ],
    )

    def validate_name(self, field):
        if Project.query.filter_by(name=field.data, user_id=current_user.id).first():
            raise ValidationError(self.ERROR_MESSAGES["name_exists"])


class ProjectFormCreate(BaseProjectForm):
    pass


class ProjectFormUpdate(BaseProjectForm):
    def __init__(self, project_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_id = project_id

    name = StringField(
        "Name",
        validators=[
            Optional(),
            Length(
                min=2, max=100, message=BaseProjectForm.size_length_message(10, 150)
            ),
        ],
    )

    def validate_name(self, field):
        if Project.query.filter(
            Project.name == field.data,
            Project.id != self.project_id,
            Project.user_id == current_user.id,
        ).first():
            raise ValidationError(self.ERROR_MESSAGES["name_exists"])
