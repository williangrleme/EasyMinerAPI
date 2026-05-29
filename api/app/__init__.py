from app.config import Config
from app.controllers import register_controllers
from app.extensions import cors, db, login_manager, migrate
from app.storage.s3_client import StorageClient
from dotenv import load_dotenv
from flask import Flask, jsonify

load_dotenv()


def create_app(config_object=None):
    app = Flask(__name__)
    app.config.from_object(config_object or Config)
    register_extensions(app)
    wire_services(app)
    register_controllers(app)
    register_home_route(app)
    return app


def register_extensions(app):
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, resources={r"/*": app.config["CORS_RESOURCES"]})
    login_manager.init_app(app)


def wire_services(app):
    from app.repositories.clean_dataset_repository import CleanDatasetRepository
    from app.repositories.dataset_repository import DatasetRepository
    from app.repositories.project_repository import ProjectRepository
    from app.repositories.user_repository import UserRepository
    from app.services.auth_service import AuthService
    from app.services.dataset_service import DatasetService
    from app.services.data_mining.cleaning_service import DataCleaningService
    from app.services.data_mining.normalization_service import DataNormalizationService
    from app.services.project_service import ProjectService
    from app.services.user_service import UserService

    session = db.session
    storage = StorageClient(
        app.config["S3_BUCKET"], app.config["S3_KEY"], app.config["S3_SECRET"]
    )

    users = UserRepository(session)
    projects = ProjectRepository(session)
    datasets = DatasetRepository(session)
    cleans = CleanDatasetRepository(session)

    # Cada domínio registra seu serviço nesta tabela conforme é implementado.
    services = {
        "auth": AuthService(users),
        "user": UserService(users, storage),
        "project": ProjectService(projects, storage),
        "dataset": DatasetService(datasets, projects, storage),
        "cleaning": DataCleaningService(datasets, cleans, storage),
        "normalization": DataNormalizationService(datasets, cleans, storage),
    }
    app.services = services


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


@login_manager.user_loader
def load_user(user_id):
    from app.models import User

    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"success": False, "message": "Não autorizado!", "errors": None}), 401
