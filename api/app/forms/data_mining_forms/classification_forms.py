import pandas as pd
from flask_wtf import FlaskForm
from wtforms import (BooleanField, FieldList, FloatField, IntegerField,
                     StringField)
from wtforms.validators import DataRequired, NumberRange


class ClassificationForm(FlaskForm):
    ERROR_MESSAGES = {
        "required": "O campo é obrigatório.",
        "column_access": "Não foi possível acessar as colunas da base de dados.",
        "invalid_features": "Os seguintes campos não estão registrados na sua base de dados: {}",
        "invalid_target": "O campo target '{}' não está registrado na sua base de dados.",
        "invalid_classification_method": "Método de classificação '{}' não é válido. Métodos válidos: {}",
        "invalid_distance_metric": "Métrica de distância '{}' não é válida. Métricas válidas: {}",
        "invalid_k": "O valor de k deve estar entre 1 e o número total de amostras de treino.",
        "insufficient_samples": "O dataset deve ter pelo menos 4 amostras para aplicar classificação.",
        "invalid_features_count": "É necessário pelo menos 1 feature para aplicar classificação.",
        "invalid_test_size": "O tamanho do conjunto de teste deve estar entre 0.1 e 0.9.",
        "target_in_features": "O campo target não pode estar incluído nas features.",
    }

    VALID_CLASSIFICATION_METHODS = ["knn"]
    VALID_DISTANCE_METRICS = ["euclidean", "manhattan", "minkowski", "mahalanobis"]

    features = FieldList(
        StringField(
            "Feature", validators=[DataRequired(message=ERROR_MESSAGES["required"])]
        )
    )

    target = StringField(
        "Target (Variável Dependente)",
        validators=[DataRequired(message=ERROR_MESSAGES["required"])],
    )

    classification_method = StringField(
        "Método de Classificação",
        validators=[DataRequired(message=ERROR_MESSAGES["required"])],
        default="knn",
    )

    distance_metric = StringField(
        "Métrica de Distância",
        validators=[DataRequired(message=ERROR_MESSAGES["required"])],
        default="euclidean",
    )

    k_neighbors = IntegerField(
        "Número de Vizinhos (k)",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
            NumberRange(min=1, message=ERROR_MESSAGES["invalid_k"]),
        ],
        default=5,
    )

    test_size = FloatField(
        "Tamanho do Conjunto de Teste (0.1 - 0.9)",
        validators=[
            DataRequired(message=ERROR_MESSAGES["required"]),
            NumberRange(min=0.1, max=0.9, message=ERROR_MESSAGES["invalid_test_size"]),
        ],
        default=0.3,
    )

    use_clean_dataset = BooleanField("Usar dataset Limpo")

    def __init__(self, file_url: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.file_url = file_url
        self.df_columns = self.load_dataframe_columns(file_url)
        self.df_size = self.get_dataframe_size(file_url)

    @staticmethod
    def load_dataframe_columns(file_url: str):
        try:
            return pd.read_csv(file_url).columns.tolist()
        except Exception as e:
            raise ValueError(f"Erro ao carregar o arquivo: {e}")

    @staticmethod
    def get_dataframe_size(file_url: str):
        try:
            return len(pd.read_csv(file_url))
        except Exception as e:
            return 0

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators=extra_validators):
            return False

        if self.df_columns is None:
            self.errors["df_columns"] = [self.ERROR_MESSAGES["column_access"]]
            return False

        if self.df_size < 4:
            self.errors["dataset"] = [self.ERROR_MESSAGES["insufficient_samples"]]
            return False

        if not self.check_features():
            return False

        if not self.check_target():
            return False

        if not self.check_classification_method():
            return False

        if not self.check_distance_metric():
            return False

        if not self.check_k_neighbors():
            return False

        if not self.check_target_not_in_features():
            return False

        if len(self.features) == 0:
            self.features.errors.append(self.ERROR_MESSAGES["invalid_features_count"])
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

    def check_target(self):
        if self.target.data not in self.df_columns:
            self.target.errors.append(
                self.ERROR_MESSAGES["invalid_target"].format(self.target.data)
            )
            return False
        return True

    def check_classification_method(self):
        if self.classification_method.data not in self.VALID_CLASSIFICATION_METHODS:
            self.classification_method.errors.append(
                self.ERROR_MESSAGES["invalid_classification_method"].format(
                    self.classification_method.data,
                    ", ".join(self.VALID_CLASSIFICATION_METHODS),
                )
            )
            return False
        return True

    def check_distance_metric(self):
        if self.distance_metric.data not in self.VALID_DISTANCE_METRICS:
            self.distance_metric.errors.append(
                self.ERROR_MESSAGES["invalid_distance_metric"].format(
                    self.distance_metric.data, ", ".join(self.VALID_DISTANCE_METRICS)
                )
            )
            return False
        return True

    def check_k_neighbors(self):
        train_size = int(self.df_size * (1 - self.test_size.data))
        if self.k_neighbors.data > train_size:
            self.k_neighbors.errors.append(self.ERROR_MESSAGES["invalid_k"])
            return False
        return True

    def check_target_not_in_features(self):
        feature_names = [feature.data for feature in self.features]
        if self.target.data in feature_names:
            self.target.errors.append(self.ERROR_MESSAGES["target_in_features"])
            return False
        return True
