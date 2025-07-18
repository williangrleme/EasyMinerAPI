from enum import Enum

import pandas as pd
from flask_wtf import FlaskForm
from wtforms import FieldList, StringField
from wtforms.validators import DataRequired, Length, ValidationError


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
    @staticmethod
    def size_length_message(min_length, max_length):
        return f"O tamanho deve estar entre {min_length} e {max_length}."

    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "invalid_method": "Opção inválida: {}. Selecione uma opção válida.",
        "invalid_missing_value": "Opção inválida: {}. Selecione uma opção válida.",
        "column_access": "Não foi possível acessar as colunas da base de dados.",
        "invalid_features": "Os seguintes campos não estão registrados na sua base de dados: {}",
    }

    features = FieldList(
        StringField(
            "Feature", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
        )
    )

    methods = StringField(
        "Methods", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
    )

    missing_values = FieldList(
        StringField(
            "Missing Value",
            validators=[DataRequired(message=ERROR_MESSAGES["required"])],
        ),
        validators=[Length(min=1, max=4, message=size_length_message(1, 4))],
    )

    def __init__(self, file_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_url = file_url
        self.df_columns = self.load_dataframe_columns(file_url)

    @staticmethod
    def load_dataframe_columns(file_url: str):
        try:
            return pd.read_csv(file_url).columns.tolist()
        except Exception as e:
            raise ValueError(f"Erro ao carregar o arquivo: {e}")

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        if self.df_columns is None:
            self.errors["df_columns"] = [self.ERROR_MESSAGES["column_access"]]
            return False

        self.validate_methods(self.methods)
        self.validate_missing_values(self.missing_values)

        if not self.check_features():
            return False

        return True

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

    def check_features(self):
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
