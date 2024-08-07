from flask import Flask, jsonify
from app.config import Config
from app.extensions import db, migrate, csrf, login_manager, cors, swagger
from dotenv import load_dotenv
from app.routes import init_routes
import os

# Carregar variáveis do .env
load_dotenv()


def create_app():
    app = Flask(__name__)

    # Carregar configurações
    app.config.from_object(Config)

    # Inicialize as extensões
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    cors.init_app(app)
    swagger.init_app(app)

    # Registrar blueprints das rotas
    init_routes(app)
    # Criar o diretório de uploads se não existir
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

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
