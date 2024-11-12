import app.response_handlers as response
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from flask import current_app


class S3Controller:
    def __init__(self):
        self.s3 = self._initialize_s3_client()
        self.bucket_name = current_app.config["S3_BUCKET"]

    @staticmethod
    def _initialize_s3_client():
        return boto3.client(
            "s3",
            aws_access_key_id=current_app.config["S3_KEY"],
            aws_secret_access_key=current_app.config["S3_SECRET"],
        )

    @staticmethod
    def _get_s3_key_from_url(file_url):
        return file_url.split("/")[-1] if file_url else None

    def upload_file_to_s3(self, file, acl="public-read"):
        try:
            self.s3.upload_fileobj(
                file,
                self.bucket_name,
                file.filename,
                ExtraArgs={"ACL": acl, "ContentType": file.content_type},
            )
            return f"https://{self.bucket_name}.s3.amazonaws.com/{file.filename}"
        except NoCredentialsError as e:
            response.log_error("Credenciais AWS não configuradas ou inválidas", e)
            return None
        except ClientError as e:
            response.log_error("Falha ao realizar upload para o S3", e)
            return None

    def delete_file_from_s3(self, file_url):
        s3_key = self._get_s3_key_from_url(file_url)
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except NoCredentialsError as e:
            response.log_error("Credenciais AWS não configuradas ou inválidas", e)
            return False
        except ClientError as e:
            response.log_error("Falha ao deletar arquivo no S3", e)
            return False
