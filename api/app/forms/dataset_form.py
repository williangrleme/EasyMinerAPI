from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models import Dataset, Project
from flask_login import current_user


class DatasetFormCreate(FlaskForm):
    def validate_name(self, field):
        if Dataset.query.filter_by(name=field.data).first():
            raise ValidationError("Dataset name already registered.")

    name = StringField(
        "Name",
        validators=[
            DataRequired(),
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
            DataRequired(),
            Length(max=100),
        ],
    )
    size_file = FloatField(
        "Size File",
        validators=[
            DataRequired(),
        ],
    )
    project_id = IntegerField(
        "Project ID",
        validators=[
            DataRequired(),
        ],
    )

    def validate_project_id(self, field):
        project = Project.query.filter_by(id=field.data).first()
        if not project:
            raise ValidationError("Project ID does not exist.")
        if project.user_id != current_user.id:
            raise ValidationError("You do not have permission to use this project.")


class DatasetFormUpdate(FlaskForm):
    def __init__(self, dataset_id, *args, **kwargs):
        super(DatasetFormUpdate, self).__init__(*args, **kwargs)
        self.dataset_id = dataset_id

    def validate_name(self, field):
        if Dataset.query.filter(
            Dataset.name == field.data, Dataset.id != self.dataset_id
        ).first():
            raise ValidationError("Dataset name already registered.")

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
    size_file = FloatField(
        "Size File",
        validators=[
            Optional(),
        ],
    )

    def validate_project_id(self, field):
        project = Project.query.filter_by(id=field.data).first()
        if not project:
            raise ValidationError("Project ID does not exist.")
        if project.user_id != current_user.id:
            raise ValidationError("You do not have permission to use this project.")
