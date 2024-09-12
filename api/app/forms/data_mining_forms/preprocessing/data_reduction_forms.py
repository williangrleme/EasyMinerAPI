from flask_wtf import FlaskForm
from wtforms import StringField, FieldList, IntegerField
from wtforms.validators import Optional, DataRequired, ValidationError
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
    def __init__(self, file_url, *args, **kwargs):
        super(DataReductionForm, self).__init__(*args, **kwargs)
        self.file_url = file_url

    features = FieldList(
        StringField(
            "Feature", validators=[DataRequired(message="O campo é obrigatório.")]
        ),
        min_entries=1,
    )

    methods = StringField(
        "Methods", validators=[DataRequired(message="O campo é obrigatório.")]
    )

    random_records = IntegerField("Random_numbers", validators=[Optional()])
    systematic_records = IntegerField("Systematic_records", validators=[Optional()])
    systematic_method = StringField("Systematic_method", validators=[Optional()])

    def validate_methods(self, field):
        if field.data not in MethodEnum._value2member_map_:
            raise ValidationError(
                f"Método inválido: {field.data}. Escolha entre 'pca', 'amostragem_aleatoria' ou 'amostragem_sistematica'."
            )

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        # Validação condicional baseada no valor do método
        method = self.methods.data

        # Verifica se o método é de amostragem aleatória e se o número de registros foi fornecido
        if method == MethodEnum.AMOSTRAGEM_ALEATORIA.value:
            if not self.random_records.data:
                self.random_records.errors.append("O campo é obrigatório.")
                return False

        # Verifica se o método é de amostragem sistemática
        elif method == MethodEnum.AMOSTRAGEM_SISTEMATICA.value:
            if not self.systematic_records.data:
                self.systematic_records.errors.append("O campo é obrigatório.")
                return False

            if (
                not self.systematic_method.data
                or self.systematic_method.data
                not in SystematicMethodEnum._value2member_map_
            ):
                self.systematic_method.errors.append(
                    "Escolha entre 'maiores' ou 'menores'."
                )
                return False

            # Validação extra: lista de features deve conter exatamente uma feature
            if len(self.features.data) != 1:
                self.features.errors.append("Apenas uma feature deve ser selecionada.")
                return False

        # Carrega o dataset para validar o tamanho da amostragem
        try:
            df = pd.read_csv(self.file_url)
        except Exception:
            raise ValidationError(
                "Não foi possível acessar as colunas da base de dados."
            )

        if (
            method == MethodEnum.AMOSTRAGEM_ALEATORIA.value
            and self.random_records.data > len(df)
        ):
            self.random_records.errors.append(
                "Amostra maior que o número de registros disponíveis."
            )
            return False

        if (
            method == MethodEnum.AMOSTRAGEM_SISTEMATICA.value
            and self.systematic_records.data > len(df)
        ):
            self.systematic_records.errors.append(
                "Amostra maior que o número de registros disponíveis."
            )
            return False

        # Validações customizadas para o campo 'features'
        columns = df.columns.tolist()
        for feature in self.features:
            if feature.data not in columns:
                self.features.errors.append(
                    "O campo enviado não está registrado na sua base de dados."
                )
                return False

        return True
