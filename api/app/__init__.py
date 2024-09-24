from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, migrate, csrf, login_manager, cors, swagger
from dotenv import load_dotenv
from app.routes import init_routes
from app.controllers.s3_controller import S3Controller

# Carregar variáveis do .env
load_dotenv()


def create_app():
    app = Flask(__name__)

    # Carregar configurações
    app.config.from_object(Config)

    # Registrar blueprints das rotas
    init_routes(app)

    # Inicialize as extensões
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/*": app.config["CORS_RESOURCES"]})
    login_manager.init_app(app)
    swagger.init_app(app)
    csrf.init_app(app)

    with app.app_context():
        app.s3_controller = S3Controller()

    # Mensagem na raiz da API
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


@login_manager.user_loader
def load_user(user_id):
    from app.models import User

    return User.query.get(int(user_id))
