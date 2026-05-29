import pandas as pd
import pytest

from app.common.errors import ValidationError
from app.data_mining.reduction.strategies import (PCAStrategy,
                                                  RandomSamplingStrategy,
                                                  SystematicSamplingStrategy,
                                                  get_strategy)


def test_random_sampling_returns_n_rows():
    df = pd.DataFrame({"a": range(10), "b": range(10)})
    result = RandomSamplingStrategy().reduce(df, features=["a"], params={"random_records": 3})
    assert len(result) == 3


def test_get_strategy_unknown():
    with pytest.raises(ValidationError):
        get_strategy("inexistente")


def test_pca_returns_components_and_target():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0, 4.0], "b": [4.0, 3.0, 2.0, 1.0], "alvo": [0, 1, 0, 1]})
    result = PCAStrategy().reduce(df, features=["a", "b"], params={"target": "alvo"})
    assert list(result.columns) == ["PC1", "PC2", "alvo"]
    assert len(result) == 4


def test_pca_requires_two_features():
    df = pd.DataFrame({"a": [1.0, 2.0, 3.0], "alvo": [0, 1, 0]})
    with pytest.raises(ValidationError):
        PCAStrategy().reduce(df, features=["a"], params={"target": "alvo"})


def test_systematic_sampling_takes_largest():
    df = pd.DataFrame({"a": [1, 5, 3, 9, 2]})
    result = SystematicSamplingStrategy().reduce(
        df, features=["a"], params={"systematic_records": 2, "systematic_method": "maiores"}
    )
    assert sorted(result["a"].tolist()) == [5, 9]


def test_reduction_endpoint_random(auth_client, s3, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    from app.services.data_mining import reduction_service as mod
    df = pd.DataFrame({"idade": range(10), "peso": range(10)})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.post(f"/api/preprocessing/data-reduction/{ds.id}",
                       json={"features": ["idade"], "methods": "amostragem_aleatoria", "random_records": 5})
    assert resp.status_code == 200
    assert "reduced_dataset" in resp.get_json()["data"]
