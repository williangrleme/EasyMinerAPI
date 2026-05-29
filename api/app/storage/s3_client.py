import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.common.errors import ExternalServiceError


class StorageClient:
    def __init__(self, bucket: str, key: str, secret: str):
        self._bucket = bucket
        self._client = boto3.client(
            "s3", aws_access_key_id=key, aws_secret_access_key=secret
        )

    @staticmethod
    def _key_from_url(file_url: str) -> str:
        return file_url.split("/")[-1]

    def upload(self, file, acl: str = "public-read") -> str:
        try:
            self._client.upload_fileobj(
                file, self._bucket, file.filename,
                ExtraArgs={"ACL": acl, "ContentType": file.content_type},
            )
            return f"https://{self._bucket}.s3.amazonaws.com/{file.filename}"
        except (BotoCoreError, ClientError) as exc:
            raise ExternalServiceError("Erro ao realizar upload para o S3") from exc

    def delete(self, file_url: str) -> bool:
        if not file_url:
            return True
        try:
            self._client.delete_object(Bucket=self._bucket, Key=self._key_from_url(file_url))
            return True
        except (BotoCoreError, ClientError) as exc:
            raise ExternalServiceError("Erro ao deletar arquivo no S3") from exc
