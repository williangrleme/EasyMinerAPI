from flask_wtf import FlaskForm
from wtforms import StringField, FieldList
from wtforms.validators import Optional, DataRequired, ValidationError
from flask import current_app
import pandas as pd
import io


class DataCleaningForm(FlaskForm):
    def __init__(self, file_url, *args, **kwargs):
        super(DataCleaningForm, self).__init__(*args, **kwargs)
        self.file_url = file_url

    target = StringField(
        "Target",
        validators=[DataRequired(message="O campo é obrigatório.")],
    )
    features = FieldList(StringField("Feature", validators=[Optional()]), min_entries=1)

    def get_s3_columns(self, file_url):
        s3Controller = current_app.s3_controller
        try:
            s3_key = file_url.split("/")[-1]
            s3_object = s3Controller.s3.get_object(
                Bucket=s3Controller.bucket_name, Key=s3_key
            )
            csv_content = s3_object["Body"].read().decode("utf-8")
            df = pd.read_csv(io.StringIO(csv_content))
            columns = df.columns.tolist()
            return columns
        except Exception as e:
            return []  # Retorna uma lista vazia em caso de erro

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        columns = self.get_s3_columns(self.file_url)
        if not columns:
            raise ValidationError(
                "Não foi possível acessar as colunas da base de dados."
            )

        # Validações customizadas para o campo 'target'
        if self.target.data not in columns:
            self.target.errors.append(
                "O campo enviado não está registrado na sua base de dados."
            )
            return False

        # Validações customizadas para o campo 'features'
        for feature in self.features:
            if feature.data not in columns:
                self.features.errors.append(
                    "O campo enviado não está registrado na sua base de dados."
                )
                return False
        return True
