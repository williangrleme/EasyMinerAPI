import pandas as pd
from flask_wtf import FlaskForm
from wtforms import BooleanField, FieldList, StringField
from wtforms.validators import DataRequired, ValidationError


class DataVisualizationForm(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "column_access": "Não foi possível acessar as colunas da base de dados.",
        "invalid_features": "Os seguintes campos não estão registrados na sua base de dados: {}",
        "invalid_boolean": "O valor deve ser True ou False.",
        "invalid_central_tendency_method": "Método de visualização '{}' não é válido. Métodos válidos para tendência central: {}",
        "invalid_dispersion_method": "Método de visualização '{}' não é válido. Métodos válidos para dispersão: {}"
    }

    CENTRAL_TENDENCY_METHODS = [
        'frequency_distribution', 'mode', 'midpoint', 'median',
        'weighted_average', 'mean_frequency_distribution',
        'geometric_mean', 'harmonic_mean'
    ]

    DISPERSION_METHODS = [
        'amplitude', 'standard_deviation', 'variance', 'variation_coefficient'
    ]

    VALID_VISUALIZATION_METHODS = CENTRAL_TENDENCY_METHODS + DISPERSION_METHODS

    features = FieldList(
        StringField(
            "Feature", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
        )
    )

    use_clean_dataset = BooleanField("Usar dataset Limpo")

    visualization_method = StringField(
        "Método de Visualização",
        validators=[DataRequired(message=ERROR_MESSAGES["required"])]
    )

    def __init__(self, file_url: str, method_type: str = "all", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_url = file_url
        self.method_type = method_type
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

        if not self.check_visualization_method():
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

    def check_visualization_method(self):
        method = self.visualization_method.data

        if self.method_type == "central_tendency":
            if method not in self.CENTRAL_TENDENCY_METHODS:
                self.visualization_method.errors.append(
                    self.ERROR_MESSAGES["invalid_central_tendency_method"].format(
                        method,
                        ", ".join(self.CENTRAL_TENDENCY_METHODS)
                    )
                )
                return False

        elif self.method_type == "dispersion":
            if method not in self.DISPERSION_METHODS:
                self.visualization_method.errors.append(
                    self.ERROR_MESSAGES["invalid_dispersion_method"].format(
                        method,
                        ", ".join(self.DISPERSION_METHODS)
                    )
                )
                return False

        else:
            if method not in self.VALID_VISUALIZATION_METHODS:
                if method in self.CENTRAL_TENDENCY_METHODS:
                    error_msg = self.ERROR_MESSAGES["invalid_central_tendency_method"]
                    valid_methods = ", ".join(self.CENTRAL_TENDENCY_METHODS)
                else:
                    error_msg = self.ERROR_MESSAGES["invalid_dispersion_method"]
                    valid_methods = ", ".join(self.DISPERSION_METHODS)

                self.visualization_method.errors.append(
                    error_msg.format(method, valid_methods)
                )
                return False

        return True
