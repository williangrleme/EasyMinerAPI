from flask_wtf.file import FileField, FileAllowed
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models import Dataset, Project
from flask_login import current_user

from api.app.forms.project_form import BaseProjectForm


class DatasetFormBase(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "name_exists": "O nome da base de dados já existe.",
        "project_not_found": "O projeto não existe.",
        "access_denied": "Você não tem permissão para acessar esse projeto.",
        "size_length": "Tamanho deve estar entre {} e {}.",
        "file_allowed": "Apenas arquivos {}  são permitidos.",
    }

    @staticmethod
    def size_length_message(min_length, max_length):
        return f"O tamanho deve estar entre {min_length} e {max_length} caracteres."

    name = StringField(
        "Name",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
            Length(min=2, max=100, message=size_length_message(2, 100)),
        ],
    )

    description = StringField(
        "Description",
        validators=[
            Optional(),
            Length(min=10, max=2000, message=size_length_message(100, 2000)),
        ],
    )

    project_id = IntegerField(
        "Project ID",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
        ],
    )

    csv_file = FileField(
        "CSV File",
        validators=[
            FileAllowed(["csv"], ERROR_MESSAGES["file_allowed"].format("CSV")),
            DataRequired(message=ERROR_MESSAGES["required"]),
        ],
    )

    def validate_name(self, field):
        if Dataset.query.filter_by(name=field.data).first():
            raise ValidationError(self.ERROR_MESSAGES["name_exists"])

    def validate_project_id(self, field):
        project = Project.query.filter_by(id=field.data).first()
        if not project:
            raise ValidationError(self.ERROR_MESSAGES["project_not_found"])
        if project.user_id != current_user.id:
            raise ValidationError(self.ERROR_MESSAGES["access_denied"])


class DatasetFormCreate(DatasetFormBase):
    pass


class DatasetFormUpdate(DatasetFormBase):
    def __init__(self, dataset_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dataset_id = dataset_id

    name = StringField(
        "Name",
        validators=[
            Optional(),
            Length(
                min=2, max=100, message=BaseProjectForm.size_length_message(10, 100)
            ),
        ],
    )

    project_id = IntegerField(
        "Project ID",
        validators=[
            Optional(),
        ],
    )

    csv_file = FileField(
        "CSV File",
        validators=[
            FileAllowed(
                ["csv"], DatasetFormBase.ERROR_MESSAGES["file_allowed"].format("CSV")
            ),
            Optional(),
        ],
    )

    def validate_name(self, field):
        if Dataset.query.filter(
            Dataset.name == field.data, Dataset.id != self.dataset_id
        ).first():
            raise ValidationError(self.ERROR_MESSAGES["name_exists"])
