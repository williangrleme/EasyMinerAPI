import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    S3_KEY = os.getenv("S3_KEY")
    S3_BUCKET = os.getenv("S3_BUCKET")
    S3_SECRET = os.getenv("S3_SECRET")
    CORS_RESOURCES = {
        "origins": "*",
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "supports_credentials": True,
        "allow_headers": ["Content-Type"],
    }
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    S3_BUCKET = "test-bucket"
    S3_KEY = "test-key"
    S3_SECRET = "test-secret"
    SESSION_COOKIE_SECURE = False
    LOGIN_DISABLED = False
    WTF_CSRF_ENABLED = False
