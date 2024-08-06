import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    USER_MASTER = int(os.getenv("USER_MASTER"))
    SWAGGER = {
        'title': 'EasyMinerAPI',
        'uiversion': 3
    }
