from flask_wtf import FlaskForm
from wtforms import StringField, FieldList
from wtforms.validators import DataRequired, ValidationError, Length
import pandas as pd
from enum import Enum


class MethodEnum(Enum):
    MEAN = "media"
    MEDIAN = "mediana"
    MODE = "moda"


class MissingValuesEnum(Enum):
    NULL = "null"
    EMPTY_STRING = ""
    QUESTION_MARK = "?"
    ZERO = "0"


class DataCleaningForm(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "invalid_method": "Opção inválida: {}. Selecione uma opção válida.",
        "invalid_missing_value": "Opção inválida: {}. Selecione uma opção válida.",
        "column_access": "Não foi possível acessar as colunas da base de dados.",
        "invalid_features": "Os seguintes campos não estão registrados na sua base de dados: {}",
    }

    def __init__(self, file_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_url = file_url
        self.df_columns = self.load_dataframe_columns(file_url)

    def load_dataframe_columns(self, file_url: str):
        try:
            return pd.read_csv(file_url).columns.tolist()
        except Exception as e:
            raise ValueError(f"Erro ao carregar o arquivo: {e}")

    features = FieldList(
        StringField(
            "Feature", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
        ),
        min_entries=1,
    )

    methods = StringField(
        "Methods", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
    )

    missing_values = FieldList(
        StringField(
            "Missing Value",
            validators=[DataRequired(message=ERROR_MESSAGES["required"])],
        ),
        validators=[
            Length(min=1, max=4, message="Você deve fornecer entre 1 e 4 valores.")
        ],
    )

    def validate_methods(self, field):
        if field.data not in MethodEnum._value2member_map_:
            raise ValidationError(
                self.ERROR_MESSAGES["invalid_method"].format(field.data)
            )

    def validate_missing_values(self, field):
        valid_choices = {tag.value for tag in MissingValuesEnum}
        for missing_value in field:
            if missing_value.data not in valid_choices:
                raise ValidationError(
                    self.ERROR_MESSAGES["invalid_missing_value"].format(
                        missing_value.data
                    )
                )

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        if not self.df_columns:
            raise ValidationError(self.ERROR_MESSAGES["column_access"])

        invalid_features = [
            feature.data
            for feature in self.features
            if feature.data not in self.df_columns
        ]
        if invalid_features:
            self.features.errors.append(
                self.ERROR_MESSAGES["invalid_features"].format(
                    ", ".join(invalid_features)
                )
            )
            return False

        return True
