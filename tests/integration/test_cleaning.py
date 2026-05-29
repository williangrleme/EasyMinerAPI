import pandas as pd
import pytest

from app.common.errors import ValidationError
from app.data_mining.cleaning.strategies import (MeanFillStrategy,
                                                 ModeFillStrategy, get_strategy)


def test_mean_strategy_fills_na():
    s = pd.Series([1.0, None, 3.0])
    result = MeanFillStrategy().apply(s)
    assert result.isna().sum() == 0
    assert round(result.iloc[1], 1) == 2.0


def test_mode_strategy_fills_with_most_frequent():
    s = pd.Series([5.0, 5.0, None, 9.0])
    result = ModeFillStrategy().apply(s)
    assert result.isna().sum() == 0
    assert result.iloc[2] == 5.0


def test_mode_strategy_all_missing_raises():
    with pytest.raises(ValidationError):
        ModeFillStrategy().apply(pd.Series([None, None], dtype="float64"))


def test_get_strategy_unknown():
    import pytest
    from app.common.errors import ValidationError
    with pytest.raises(ValidationError):
        get_strategy("inexistente")


def test_data_cleaning_endpoint(auth_client, s3, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    from app.services.data_mining import cleaning_service as mod
    df = pd.DataFrame({"idade": [10, 0, 30], "peso": [50, 60, 70]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    payload = {"features": ["idade"], "methods": "media", "missing_values": ["0"]}
    resp = client.post(f"/api/preprocessing/data-cleaning/{ds.id}", json=payload)
    assert resp.status_code == 200
    assert "clean_dataset" in resp.get_json()["data"]
