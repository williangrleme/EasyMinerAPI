import pandas as pd

from app.data_mining.visualization.measures import (
    CENTRAL_TENDENCY, DISPERSION, get_median_results, get_variance_results,
)


def test_median_results(monkeypatch):
    import app.data_mining.visualization.measures as mod
    df = pd.DataFrame({"idade": [10, 20, 30]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    result = get_median_results("fake", ["idade"])
    assert result["idade"] == 20


def test_variance_results(monkeypatch):
    import app.data_mining.visualization.measures as mod
    df = pd.DataFrame({"idade": [10, 20, 30]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    result = get_variance_results("fake", ["idade"])
    assert result["idade"] == 100.0


def test_registries_have_methods():
    assert "median" in CENTRAL_TENDENCY
    assert "variance" in DISPERSION


def test_central_tendency_endpoint(auth_client, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    import app.data_mining.visualization.measures as mod
    df = pd.DataFrame({"idade": [10, 20, 30, 40]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.post(f"/api/data-visualization/measure-central-tendency/{ds.id}",
                       json={"features": ["idade"], "visualization_method": "median"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["idade"] == 25


def test_association_requires_two_features(auth_client, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    import app.data_mining.visualization.measures as mod
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.post(f"/api/data-visualization/association-measure/{ds.id}",
                       json={"features": ["a"], "visualization_method": "correlation"})
    assert resp.status_code == 422
