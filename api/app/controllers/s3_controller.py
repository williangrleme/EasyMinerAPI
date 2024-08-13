from flask import current_app
import boto3
from botocore.exceptions import NoCredentialsError


class S3Controller:
    # Inializa o s3 no construtor
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
            return f"https://{self.bucket_name}.s3.amazonaws.com/{file.filename}"
        except Exception as e:
            # Loga o erro em caso de falha no upload
            current_app.logger.error(f"falha ao realizar upload para o S3: {e}")
            return str(e)

    def delete_file_from_s3(self, file_url):
        s3_key = file_url.split("/")[-1]  # Extrai a chave do arquivo a partir da URL
        try:
            self.s3.delete_object(Bucket=self.bucket_name, Key=s3_key)
        except NoCredentialsError:
            # Retorna False se houver erro de credenciais
            return False
        return True
