import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USER_MASTER = int(os.getenv("USER_MASTER"))
    SWAGGER = {"title": "EasyMinerAPI", "uiversion": 3}
    UPLOAD_FOLDER = os.getenv(
        "UPLOAD_FOLDER", default=os.path.join(os.getcwd(), "uploads")
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # Limite de 16MB
