import boto3
import pytest
from moto import mock_aws

from app.config import TestConfig
from app.extensions import db as _db


@pytest.fixture()
def app():
    from app import create_app
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def s3(app):
    with mock_aws():
        conn = boto3.client(
            "s3",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-east-1",
        )
        conn.create_bucket(Bucket="test-bucket")
        yield conn


@pytest.fixture()
def auth_client(client, db):
    from tests.factories import make_user

    user = make_user()
    resp = client.post(
        "/api/auth/login", json={"email": user.email, "password": "senha1234"}
    )
    assert resp.status_code == 200, f"auth_client login falhou: {resp.get_json()}"
    return client, user
