from app.config import Config
from app.controllers.s3_controller import S3Controller
from app.extensions import cors, db, login_manager, migrate
from app.response_handlers import register_response_errors
from app.routes import init_routes
from dotenv import load_dotenv
from flask import Flask, jsonify

load_dotenv()


def create_app(config_object=None):
    app = Flask(__name__)
    configure_app(app, config_object)
    register_extensions(app)
    register_blueprints(app)
    register_home_route(app)
    initialize_s3_controller(app)
    register_response_errors(app)
    return app


def configure_app(app, config_object=None):
    app.config.from_object(config_object or Config)


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/*": app.config["CORS_RESOURCES"]})
    login_manager.init_app(app)


def register_blueprints(app):
    init_routes(app)


def register_home_route(app):
    @app.route("/", methods=["GET"])
    def home():
        return (
            jsonify(
                {
                    "Mensagem": "Bem-vindo a API do EasyMiner",
                    "OBS": "Para ter acesso a documentação acesse a URL /apidocs",
                }
            ),
            200,
        )


def initialize_s3_controller(app):
    with app.app_context():
        app.s3_controller = S3Controller()


@login_manager.user_loader
def load_user(user_id):
    from app.models import User

    return User.query.get(int(user_id))
