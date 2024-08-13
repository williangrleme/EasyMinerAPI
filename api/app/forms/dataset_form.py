from flask_wtf.file import FileField, FileAllowed
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models import Dataset, Project
from flask_login import current_user


class DatasetFormCreate(FlaskForm):
    def validate_name(self, field):
        if Dataset.query.filter_by(name=field.data).first():
            raise ValidationError("O nome da base de dados já existe.")

    name = StringField(
        "Name",
        validators=[
            DataRequired(message="O campo é obrigatório."),
            Length(min=3, max=255),
        ],
    )
    description = StringField(
        "Description",
        validators=[
            Optional(),
            Length(min=11, max=2000),
        ],
    )
    target = StringField(
        "Target",
        validators=[
            DataRequired(message="O campo é obrigatório."),
            Length(max=100),
        ],
    )

    project_id = IntegerField(
        "Project ID",
        validators=[
            DataRequired(message="O campo é obrigatório."),
        ],
    )

    csv_file = FileField(
        "CSV File",
        validators=[
            FileAllowed(["csv"], "Apenas arquivos CSV são permitidos."),
            DataRequired(message="O campo é obrigatório."),
        ],
    )

    def validate_project_id(self, field):
        project = Project.query.filter_by(id=field.data).first()
        if not project:
            raise ValidationError("O projeto não existe")
        if project.user_id != current_user.id:
            raise ValidationError("Você não tem permissão para acessar esse projeto")


class DatasetFormUpdate(FlaskForm):
    def __init__(self, dataset_id, *args, **kwargs):
        super(DatasetFormUpdate, self).__init__(*args, **kwargs)
        self.dataset_id = dataset_id

    def validate_name(self, field):
        if Dataset.query.filter(
            Dataset.name == field.data, Dataset.id != self.dataset_id
        ).first():
            raise ValidationError("O nome da base de dados já existe.")

    name = StringField(
        "Name",
        validators=[
            Optional(),
            Length(min=3, max=255),
        ],
    )
    description = StringField(
        "Description",
        validators=[
            Optional(),
            Length(min=11, max=2000),
        ],
    )
    target = StringField(
        "Target",
        validators=[
            Optional(),
            Length(max=100),
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
            FileAllowed(["csv"], "Apenas arquivos CSV são permitidos."),
            Optional(),
        ],
    )

    def validate_project_id(self, field):
        project = Project.query.filter_by(id=field.data).first()
        if not project:
            raise ValidationError("O projeto não existe")
        if project.user_id != current_user.id:
            raise ValidationError("Você não tem permissão para acessar esse projeto")
