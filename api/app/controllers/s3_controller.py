from flask import jsonify, current_app
import boto3
from botocore.exceptions import NoCredentialsError, ClientError


class S3Controller:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=current_app.config["S3_KEY"],
            aws_secret_access_key=current_app.config["S3_SECRET"],
        )
        self.bucket_name = current_app.config["S3_BUCKET"]

    def upload_file_to_s3(self, file, acl="public-read"):
        try:
            self.s3.upload_fileobj(
                file,
                self.bucket_name,
                file.filename,
                ExtraArgs={"ACL": acl, "ContentType": file.content_type},
            )
            file_url = f"https://{self.bucket_name}.s3.amazonaws.com/{file.filename}"
            return (
                jsonify(
                    {
                        "message": "Upload realizado com sucesso!",
                        "success": True,
                        "data": {"file_url": file_url},
                    }
                ),
                200,
            )
        except ClientError as e:
            current_app.logger.error(f"Falha ao realizar upload para o S3: {e}")
            return (
                jsonify(
                    {
                        "message": "Falha ao realizar upload para o S3.",
                        "success": False,
                        "data": str(e),
                    }
                ),
                500,
            )

    def delete_file_from_s3(self, file_url):
        s3_key = file_url.split("/")[-1]
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
            return (
                jsonify(
                    {
                        "message": "Arquivo deletado com sucesso!",
                        "success": True,
                        "data": None,
                    }
                ),
                200,
            )
        except NoCredentialsError:
            return (
                jsonify(
                    {
                        "message": "Credenciais inválidas para acesso ao S3.",
                        "success": False,
                        "data": None,
                    }
                ),
                403,
            )
        except ClientError as e:
            current_app.logger.error(f"Falha ao deletar arquivo no S3: {e}")
            return (
                jsonify(
                    {
                        "message": "Falha ao deletar arquivo no S3.",
                        "success": False,
                        "data": str(e),
                    }
                ),
                500,
            )
