from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, ValidationError, Optional

from app.models import Project


class ProjectFormCreate(FlaskForm):
    def validate_name(self, field):
        if Project.query.filter_by(name=field.data).first():
            raise ValidationError("Project name already registered.")

    name = StringField(
        "Name",
        validators=[
            DataRequired(),
            Length(min=3, max=200),
        ],
    )
    description = StringField(
        "Description",
        validators=[
            Optional(),
            Length(min=11, max=2000),
        ],
    )


class ProjectFormUpdate(FlaskForm):
    def __init__(self, project_id, *args, **kwargs):
        super(ProjectFormUpdate, self).__init__(*args, **kwargs)
        self.project_id = project_id

    def validate_name(self, field):
        if Project.query.filter(
            Project.name == field.data, Project.id != self.project_id
        ).first():
            raise ValidationError("Project name already registered.")

    name = StringField(
        "Name",
        validators=[
            Optional(),
            Length(min=3, max=200),
        ],
    )
    description = StringField(
        "Description",
        validators=[
            Optional(),
            Length(min=11, max=2000),
        ],
    )
