from flask_wtf import FlaskForm
from wtforms import StringField, FieldList
from wtforms.validators import DataRequired, ValidationError
import pandas as pd
from enum import Enum


class MethodEnum(Enum):
    MINMAX = "minmax"
    ZSCORE = "zscore"


class DataNormalizationForm(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "invalid_method": "Método inválido: {}. Selecione uma opção válida.",
        "column_access": "Não foi possível acessar as colunas da base de dados.",
        "invalid_features": "Os seguintes campos não estão registrados na sua base de dados: {}",
    }

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

    features = FieldList(
        StringField(
            "Feature", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
        ),
    )

    methods = StringField(
        "Methods", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
    )

    def validate_methods(self, field):
        if field.data not in MethodEnum._value2member_map_:
            raise ValidationError(
                self.ERROR_MESSAGES["invalid_method"].format(field.data)
            )

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        if not self.df_columns:
            raise ValidationError(self.ERROR_MESSAGES["column_access"])

        if not self.check_features():
            return False

        return True

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
