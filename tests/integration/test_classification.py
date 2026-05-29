import pandas as pd
import pytest

from app.common.errors import ValidationError
from app.data_mining.classification.strategies import KNNStrategy, get_strategy

_DF = pd.DataFrame({
    "x": [1, 2, 3, 4, 5, 6, 7, 8],
    "y": [1, 2, 3, 4, 5, 6, 7, 8],
    "label": [0, 0, 0, 0, 1, 1, 1, 1],
})


def test_knn_strategy_returns_metrics():
    result = KNNStrategy().run(_DF, features=["x", "y"], target="label",
                               params={"k_neighbors": 3, "distance_metric": "euclidean", "test_size": 0.25})
    assert "performance_metrics" in result
    assert result["algorithm_info"]["k_neighbors"] == 3


def test_get_strategy_unknown():
    with pytest.raises(ValidationError):
        get_strategy("svm")


def test_knn_k_larger_than_train_raises():
    with pytest.raises(ValidationError):
        KNNStrategy().run(_DF, features=["x", "y"], target="label",
                          params={"k_neighbors": 99, "distance_metric": "euclidean", "test_size": 0.25})


def test_knn_single_feature_plot_has_empty_y():
    result = KNNStrategy().run(_DF, features=["x"], target="label",
                               params={"k_neighbors": 3, "distance_metric": "euclidean", "test_size": 0.25})
    assert result["plot_algorithm"]["y"] == []


def test_classification_endpoint(auth_client, s3, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    from app.services.data_mining import classification_service as mod
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8],
        "y": [1, 2, 3, 4, 5, 6, 7, 8],
        "label": [0, 0, 0, 0, 1, 1, 1, 1],
    })
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    payload = {"features": ["x", "y"], "target": "label", "classification_method": "knn",
               "k_neighbors": 3, "test_size": 0.25}
    resp = client.post(f"/api/classification/{ds.id}", json=payload)
    assert resp.status_code == 200
    assert "performance_metrics" in resp.get_json()["data"]
