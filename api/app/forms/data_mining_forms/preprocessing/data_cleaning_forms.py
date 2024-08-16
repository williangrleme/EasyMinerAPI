from flask_wtf import FlaskForm
from wtforms import StringField, FieldList
from wtforms.validators import Optional, DataRequired, ValidationError
import pandas as pd
from enum import Enum


class MethodEnum(Enum):
    MEAN = "mean"
    MEDIAN = "median"
    MODE = "mode"


class DataCleaningForm(FlaskForm):
    def __init__(self, file_url, *args, **kwargs):
        super(DataCleaningForm, self).__init__(*args, **kwargs)
        self.file_url = file_url

    target = StringField(
        "Target",
        validators=[DataRequired(message="O campo é obrigatório.")],
    )

    features = FieldList(StringField("Feature", validators=[Optional()]), min_entries=1)

    methods = StringField(
        "Methods", validators=[DataRequired(message="O campo é obrigatório.")]
    )

    # Validação customizada para o campo 'methods'
    def validate_methods(self, field):
        if field.data not in MethodEnum._value2member_map_:
            raise ValidationError(
                f"Método inválido: {field.data}. Escolha entre 'mean', 'median' ou 'mode'."
            )

    def validate(self, **kwargs):
        if not super().validate(**kwargs):
            return False

        df = pd.read_csv(self.file_url, na_values="?")
        columns = df.columns.tolist()

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
