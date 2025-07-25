import app.response_handlers as response
import pandas as pd
from app.forms.data_mining_forms.classification_forms import ClassificationForm
from app.models import CleanDataset, Dataset
from flask_login import current_user
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier


def classification_algorithm(dataset_id):
    try:
        dataset = (
            Dataset.query.outerjoin(CleanDataset, Dataset.id == CleanDataset.dataset_id)
            .filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id)
            .with_entities(
                Dataset.id,
                Dataset.file_url,
                CleanDataset.file_url.label("clean_file_url"),
            )
            .first()
        )

        if not dataset:
            return response.handle_not_found_response("Base de dados não encontrada!")

        form = ClassificationForm(file_url=dataset.file_url)
        if not form.validate_on_submit():
            return response.handle_unprocessable_entity(form.errors)

        if form.use_clean_dataset.data:
            if dataset.clean_file_url:
                file_url = dataset.clean_file_url
            else:
                return response.handle_not_found_response(
                    "Dataset limpo não encontrado!"
                )
        else:
            file_url = dataset.file_url

        results = execute_classification_algorithm(
            file_url=file_url,
            features=[f.data for f in form.features],
            target=form.target.data,
            classification_method=form.classification_method.data,
            k_neighbors=form.k_neighbors.data,
            distance_metric=form.distance_metric.data,
            test_size=form.test_size.data,
        )

        return response.handle_success(
            f"Algoritmo de classificação {form.classification_method.data.upper()} executado com sucesso!",
            results,
        )

    except Exception as e:
        return response.handle_internal_server_error_response(
            e, "Erro ao executar algoritmo de classificação!"
        )


def execute_classification_algorithm(
    file_url,
    features,
    target,
    classification_method,
    k_neighbors,
    distance_metric,
    test_size,
):
    try:
        df = pd.read_csv(file_url)

        X = df[features]
        y = df[target]

        if X.isnull().any().any() or y.isnull().any():
            mask = ~(X.isnull().any(axis=1) | y.isnull())
            X = X[mask]
            y = y[mask]

            if len(X) == 0:
                raise ValueError(
                    "Todas as amostras possuem valores ausentes nas features ou target selecionadas"
                )

        if classification_method == "knn":
            results = execute_knn_classification(
                X, y, features, target, k_neighbors, distance_metric, test_size
            )
        else:
            raise ValueError(
                f"Método de classificação '{classification_method}' não implementado"
            )

        return results

    except Exception as e:
        raise ValueError(f"Erro ao executar algoritmo de classificação: {e}")


def execute_knn_classification(
    X, y, features, target, k_neighbors, distance_metric, test_size
):
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=42, stratify=y
        )

        knn = KNeighborsClassifier(n_neighbors=k_neighbors, metric=distance_metric)
        knn.fit(X_train, y_train)

        y_pred = knn.predict(X_test)

        class_report = classification_report(
            y_test, y_pred, output_dict=True, zero_division=0
        )

        conf_matrix = confusion_matrix(y_test, y_pred)

        results = {
            "algorithm_info": {
                "name": "K-Nearest Neighbors",
                "type": "Classification",
                "k_neighbors": k_neighbors,
                "distance_metric": distance_metric,
                "features_used": features,
                "target": target,
            },
            "dataset_info": {
                "total_samples": len(X),
                "features_count": len(features),
                "train_samples": len(X_train),
                "test_samples": len(X_test),
                "test_size_percentage": round(test_size * 100, 2),
                "unique_classes": len(y.unique()),
                "class_distribution": y.value_counts().to_dict(),
            },
            "performance_metrics": class_report,
            "confusion_matrix": conf_matrix.tolist(),
            "plot_algorithm": {
                "x": X_test.iloc[:, 0].tolist(),
                "y": X_test.iloc[:, 1].tolist(),
                "predicted_labels": y_pred.tolist(),
                "true_labels": y_test.tolist(),
            },
        }

        return results

    except Exception as e:
        raise ValueError(f"Erro ao executar KNN classification: {e}")
