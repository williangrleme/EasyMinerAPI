import pandas as pd

from app.data_mining.normalization.strategies import get_strategy, MinMaxStrategy


def test_minmax_scales_0_1():
    s = pd.Series([0.0, 5.0, 10.0])
    result = MinMaxStrategy().apply(s)
    assert round(result.min(), 4) == 0.0
    assert round(result.max(), 4) == 1.0


def test_get_strategy_unknown():
    import pytest
    from app.common.errors import ValidationError
    with pytest.raises(ValidationError):
        get_strategy("xpto")


def test_normalization_endpoint(auth_client, s3, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    from app.services.data_mining import normalization_service as mod
    df = pd.DataFrame({"idade": [10.0, 20.0, 30.0]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.post(f"/api/preprocessing/data-normalization/{ds.id}",
                       json={"features": ["idade"], "methods": "minmax"})
    assert resp.status_code == 200
    assert "normalized_dataset" in resp.get_json()["data"]
