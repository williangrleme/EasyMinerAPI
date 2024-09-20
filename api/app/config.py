import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USER_MASTER = int(os.getenv("USER_MASTER"))
    SWAGGER = {"title": "EasyMinerAPI", "uiversion": 3}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite de 16MB
    S3_KEY = os.getenv("S3_KEY")
    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_SECRET = os.getenv("S3_SECRET")
    CORS_RESOURCES = {
        r"/*": {
            "origins": "*",  # Permitir qualquer origem, ou definir uma origem específica
            "methods": [
                "OPTIONS",
                "GET",
                "POST",
                "PUT",
                "DELETE",
            ],  # Métodos permitidos
            "supports_credentials": True,  # Permitir envio de cookies/credenciais
        }
    }
