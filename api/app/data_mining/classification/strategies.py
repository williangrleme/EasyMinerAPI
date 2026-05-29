from abc import ABC, abstractmethod

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

from app.common.errors import ValidationError


class ClassificationStrategy(ABC):
    name: str

    @abstractmethod
    def run(self, df: pd.DataFrame, features: list[str], target: str, params: dict) -> dict: ...


class KNNStrategy(ClassificationStrategy):
    name = "knn"

    def run(self, df, features, target, params):
        X, y = df[features], df[target]
        mask = ~(X.isnull().any(axis=1) | y.isnull())
        X, y = X[mask], y[mask]
        if len(X) == 0:
            raise ValidationError("Dados inválidos!", {"dataset": ["Todas as amostras possuem valores ausentes."]})

        k = params["k_neighbors"]
        metric = params["distance_metric"]
        test_size = params["test_size"]
        try:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=test_size, random_state=42, stratify=y
            )
        except ValueError as exc:
            raise ValidationError(
                "Dados inválidos!",
                {"dataset": [f"Não foi possível dividir os dados para treino/teste: {exc}"]},
            )
        if k > len(X_train):
            raise ValidationError(
                "Dados inválidos!",
                {"k_neighbors": [f"k ({k}) não pode ser maior que o número de amostras de treino ({len(X_train)})."]},
            )
        model = KNeighborsClassifier(n_neighbors=k, metric=metric)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        return {
            "algorithm_info": {
                "name": "K-Nearest Neighbors", "type": "Classification",
                "k_neighbors": k, "distance_metric": metric,
                "features_used": features, "target": target,
            },
            "dataset_info": {
                "total_samples": len(X), "features_count": len(features),
                "train_samples": len(X_train), "test_samples": len(X_test),
                "test_size_percentage": round(test_size * 100, 2),
                "unique_classes": len(y.unique()),
                "class_distribution": y.value_counts().to_dict(),
            },
            "performance_metrics": classification_report(y_test, y_pred, output_dict=True, zero_division=0),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "plot_algorithm": {
                "x": X_test.iloc[:, 0].tolist(),
                "y": X_test.iloc[:, 1].tolist() if X_test.shape[1] > 1 else [],
                "predicted_labels": y_pred.tolist(), "true_labels": y_test.tolist(),
            },
        }


_REGISTRY = {s.name: s for s in (KNNStrategy,)}


def get_strategy(name: str) -> ClassificationStrategy:
    strategy = _REGISTRY.get(name)
    if strategy is None:
        raise ValidationError("Dados inválidos!", {"classification_method": [f"Método '{name}' não é válido."]})
    return strategy()
