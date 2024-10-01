import os
from flask import Flask, jsonify, session
from dotenv import load_dotenv
from config import Config
from extensions import db, migrate, csrf, login_manager, cors, swagger
from routes import init_routes
from controllers.s3_controller import S3Controller


def create_app():
    # Carregar variáveis de ambiente
    load_dotenv()

    # Criar instância da aplicação Flask
    app = Flask(__name__)

    # Carregar configurações a partir do objeto Config
    app.config.from_object(Config)

    # Inicializar extensões
    initialize_extensions(app)

    # Registrar blueprints das rotas
    init_routes(app)

    # Inicializar controlador S3
    with app.app_context():
        app.s3_controller = S3Controller()

    @app.after_request
    def apply_cors(response):
        session_cookie = session.get("_id", "default_session_value")
        response.headers["Set-Cookie"] = (
            f"session={session_cookie}; SameSite=None; Secure"
        )
        return response

    # Rota raiz com mensagem de boas-vindas
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

    return app


def initialize_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/*": app.config["CORS_RESOURCES"]})
    login_manager.init_app(app)
    swagger.init_app(app)
    csrf.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    from models import User

    return User.query.get(int(user_id))
