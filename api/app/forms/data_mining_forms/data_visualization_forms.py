import pandas as pd
from flask_wtf import FlaskForm
from wtforms import BooleanField, FieldList, StringField
from wtforms.validators import DataRequired


class DataVisualizationForm(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "column_access": "Não foi possível acessar as colunas da base de dados.",
        "invalid_features": "Os seguintes campos não estão registrados na sua base de dados: {}",
        "invalid_boolean": "O valor deve ser True ou False.",
    }

    features = FieldList(
        StringField(
            "Feature", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
        )
    )

    use_clean_dataset = BooleanField("Usar dataset Limpo")

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
