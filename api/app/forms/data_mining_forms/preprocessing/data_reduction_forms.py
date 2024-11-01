from flask_wtf import FlaskForm
from wtforms import StringField, FieldList, IntegerField
from wtforms.validators import DataRequired, Optional, ValidationError
import pandas as pd
from enum import Enum


class MethodEnum(Enum):
    PCA = "pca"
    AMOSTRAGEM_ALEATORIA = "amostragem_aleatoria"
    AMOSTRAGEM_SISTEMATICA = "amostragem_sistematica"


class SystematicMethodEnum(Enum):
    MAIORES = "maiores"
    MENORES = "menores"


class DataReductionForm(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "invalid_method": "Método inválido: {}. Selecione uma opção válida.",
        "invalid_systematic_method": "Escolha entre 'maiores' ou 'menores'.",
        "feature_selection": "Apenas uma feature deve ser selecionada.",
        "column_access": "Não foi possível acessar as colunas da base de dados.",
        "invalid_features": "Os seguintes campos não estão registrados na sua base de dados: {}",
        "sample_size_exceeds_records": "Amostra maior que o número de registros disponíveis.",
    }

    features = FieldList(
        StringField(
            "Feature", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
        )
    )

    methods = StringField(
        "Methods", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
    )

    random_records = IntegerField("Random_numbers", validators=[Optional()])
    systematic_records = IntegerField("Systematic_records", validators=[Optional()])
    systematic_method = StringField("Systematic_method", validators=[Optional()])

    def __init__(self, file_url, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_url = file_url
        self.df = self.load_dataframe(file_url)

    @staticmethod
    def load_dataframe(file_url):
        try:
            return pd.read_csv(file_url)
        except Exception as e:
            raise ValueError(f"Erro ao carregar o arquivo: {e}")

    def validate_methods(self, field):
        if field.data not in MethodEnum._value2member_map_:
            raise ValidationError(
                self.ERROR_MESSAGES["invalid_method"].format(field.data)
            )

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        if self.df is None:
            raise ValidationError(self.ERROR_MESSAGES["column_access"])

        if not self.check_features():
            return False

        if not self.check_sampling_method(self.methods.data):
            return False

        return True

    def check_sampling_method(self, method):
        if method == MethodEnum.AMOSTRAGEM_ALEATORIA.value:
            return self.check_random_sampling()

        if method == MethodEnum.AMOSTRAGEM_SISTEMATICA.value:
            return self.check_systematic_sampling()

        return True

    def check_random_sampling(self):
        if not self.random_records.data:
            self.random_records.errors.append(self.ERROR_MESSAGES["required"])
            return False

        if self.random_records.data > len(self.df):
            self.random_records.errors.append(
                self.ERROR_MESSAGES["sample_size_exceeds_records"]
            )
            return False

        return True

    def check_systematic_sampling(self):
        if not self.systematic_records.data:
            self.systematic_records.errors.append(self.ERROR_MESSAGES["required"])
            return False

        if self.systematic_records.data > len(self.df):
            self.systematic_records.errors.append(
                self.ERROR_MESSAGES["sample_size_exceeds_records"]
            )
            return False

        if (
            not self.systematic_method.data
            or self.systematic_method.data
            not in SystematicMethodEnum._value2member_map_
        ):
            self.systematic_method.errors.append(
                self.ERROR_MESSAGES["invalid_method"].format(
                    self.systematic_method.data
                )
            )
            return False

        if len(self.features.data) != 1:
            self.features.errors.append(self.ERROR_MESSAGES["feature_selection"])
            return False

        return True

    def check_features(self):
        columns = self.df.columns.tolist()
        invalid_features = [
            feature.data for feature in self.features if feature.data not in columns
        ]
        if invalid_features:
            self.features.errors.append(
                self.ERROR_MESSAGES["invalid_features"].format(
                    ", ".join(invalid_features)
                )
            )
            return False
        return True
