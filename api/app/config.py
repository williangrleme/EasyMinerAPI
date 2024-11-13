import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite de 16MB
    S3_KEY = os.getenv("S3_KEY")
    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_SECRET = os.getenv("S3_SECRET")
    CORS_RESOURCES = {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True,
        "allow_headers": [
            "Content-Type",
            "X-CSRF-Token",
        ],
    }
    WTF_CSRF_ENABLED = False  # TODO: Tratar CSRF futuramente
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    SWAGGER = {
        "title": "EasyMinerAPI",
        "uiversion": 3,
        "openapi": "3.0.0",
    }
