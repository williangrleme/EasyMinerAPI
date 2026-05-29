from io import BytesIO

from app.storage.s3_client import StorageClient


def test_upload_returns_url(app, s3):
    client = StorageClient(bucket="test-bucket", key="test-key", secret="test-secret")
    upload = BytesIO(b"a,b\n1,2\n")
    upload.filename = "file123.csv"
    upload.content_type = "text/csv"
    url = client.upload(upload)
    assert url == "https://test-bucket.s3.amazonaws.com/file123.csv"


def test_delete_returns_true(app, s3):
    client = StorageClient(bucket="test-bucket", key="test-key", secret="test-secret")
    upload = BytesIO(b"x")
    upload.filename = "todelete.csv"
    upload.content_type = "text/csv"
    client.upload(upload)
    assert client.delete("https://test-bucket.s3.amazonaws.com/todelete.csv") is True
