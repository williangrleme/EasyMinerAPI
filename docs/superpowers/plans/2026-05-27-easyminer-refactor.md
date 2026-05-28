# EasyMinerAPI — Plano de Implementação da Refatoração

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reescrever a EasyMinerAPI numa arquitetura em camadas (controller → schema Pydantic → service → repository), aplicando SOLID/DRY/clean code, com testes de integração por endpoint, Swagger gerado do código, README atualizado — tudo na branch `develop`.

**Architecture:** Camadas com responsabilidade única e dependências invertidas. Controllers finos (HTTP), schemas Pydantic v2 (validação/serialização), services (regra de negócio + transação), repositories (único ponto que toca SQLAlchemy), strategies para algoritmos de data mining, `StorageClient` para S3. Boilerplate de erro/transação centralizado em decorators.

**Tech Stack:** Python 3, Flask 3, SQLAlchemy (Flask-SQLAlchemy), Pydantic v2, pandas, scikit-learn, boto3, pytest, pytest-flask, moto, flasgger.

---

## Contexto para o implementador

O projeto atual fica em `api/app/`. O Flask app é criado por `create_app()` em `api/app/__init__.py`. O `PYTHONPATH` aponta para `api/` (imports são `from app.xxx`). Há 7 blueprints registrados em `api/app/routes/__init__.py` com estes prefixos e rotas (PRESERVAR URLs e métodos):

```
/api/users    POST /            (create, público)
              PUT /             (update, login)
              DELETE /          (delete, login)
/api/auth     GET /csrf-token   (público) — REMOVER no refactor (CSRF sai)
              POST /login        (público)
              POST /logout       (login)
              GET /me            (login)
/api/projects GET /             (list, login)
              GET /<int:id>      (get, login)
              POST /            (create, login)
              PUT /<int:id>      (update, login)
              DELETE /<int:id>   (delete, login)
/api/datasets GET /             (list, login)
              GET /<int:id>      (get, login)
              POST /create-dataset (create, login)
              PUT /<int:id>      (update, login)
              DELETE /<int:id>   (delete, login)
/api/preprocessing       POST /data-cleaning/<int:id>      (login)
                         POST /data-normalization/<int:id> (login)
                         POST /data-reduction/<int:id>     (login)
/api/data-visualization  POST /measure-central-tendency/<int:id> (login)
                         POST /dispersion-measure/<int:id>        (login)
                         POST /shape-measure/<int:id>             (login)
                         POST /association-measure/<int:id>       (login)
/api/classification      POST /<int:id>                    (login)
```

**Quebras de contrato permitidas** (decisão do dono): padronizar envelope de resposta, formato de erro de validação (Pydantic em vez de WTForms dict) e remover CSRF/`/csrf-token`. URLs, métodos e status codes permanecem.

**Modelos SQLAlchemy** (mantidos quase iguais): `User`, `Project`, `Dataset`, `CleanDataset` em `api/app/models/`. Relações com `cascade="all, delete-orphan"`. `CleanDataset` tem um listener `after_delete` que apaga o arquivo do S3 — esse listener será REMOVIDO (a remoção de arquivo S3 passa a ser responsabilidade explícita do service, evitando IO escondido dentro do ORM).

**Convenção de commits:** seguir o padrão do repo: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`. Identidade git não está configurada globalmente — use:
`git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit ...`

---

## Estrutura de arquivos final

```
api/app/
  __init__.py                      # create_app + wiring
  config.py                        # Config (remove CSRF/SESSION CSRF)
  extensions.py                    # db, migrate, login_manager, cors (remove csrf, swagger template)
  common/
    __init__.py
    errors.py                      # DomainError + subclasses
    responses.py                   # success_response / error_response (envelope)
    decorators.py                  # handle_errors, transactional
    files.py                       # helpers de CSV/tamanho (DRY)
  storage/
    __init__.py
    s3_client.py                   # StorageClient (encapsula boto3)
  repositories/
    __init__.py
    base.py                        # BaseRepository
    user_repository.py
    project_repository.py
    dataset_repository.py
    clean_dataset_repository.py
  schemas/
    __init__.py
    auth.py
    user.py
    project.py
    dataset.py
    data_mining/
      __init__.py
      cleaning.py
      normalization.py
      reduction.py
      classification.py
      visualization.py
  services/
    __init__.py
    auth_service.py
    user_service.py
    project_service.py
    dataset_service.py
    data_mining/
      __init__.py
      cleaning_service.py
      normalization_service.py
      reduction_service.py
      classification_service.py
      visualization_service.py
  data_mining/
    __init__.py
    cleaning/strategies.py         # MissingValueStrategy + impls + registry
    normalization/strategies.py    # NormalizationStrategy + impls + registry
    reduction/strategies.py        # ReductionStrategy + impls + registry
    classification/strategies.py   # ClassificationStrategy + impls + registry
    visualization/measures.py      # funções de medida + registries
  controllers/
    __init__.py                    # register_controllers(app)
    auth_controller.py
    user_controller.py
    project_controller.py
    dataset_controller.py
    data_mining/
      __init__.py
      preprocessing_controller.py
      visualization_controller.py
      classification_controller.py
  models/                          # mantidos; clean_dataset.py perde o event listener
  docs/openapi.py                  # geração de spec (Task Swagger)

tests/
  __init__.py
  conftest.py
  factories.py
  integration/
    __init__.py
    test_auth.py
    test_users.py
    test_projects.py
    test_datasets.py
    test_cleaning.py
    test_normalization.py
    test_reduction.py
    test_classification.py
    test_visualization.py
```

Pastas REMOVIDAS ao final: `api/app/forms/`, `api/app/controllers/s3_controller.py` (vira `storage/s3_client.py`), `api/app/response_handlers.py` (vira `common/`), `api/app/swagger/swagger.yaml`, e os controllers antigos procedurais (substituídos).

---

## Ordem de execução

Tasks 1–4 são fundação (sem elas nada compila). Tasks 5–8 são domínios CRUD independentes entre si. Tasks 9–13 são data mining (dependem de datasets). Tasks 14–17 finalizam (wiring, limpeza, swagger, readme, push). Cada task termina com commit.

---

## Task 1: Camada `common/` (erros, respostas, decorators)

**Files:**
- Create: `api/app/common/__init__.py` (vazio)
- Create: `api/app/common/errors.py`
- Create: `api/app/common/responses.py`
- Create: `api/app/common/decorators.py`
- Create: `api/app/common/files.py`
- Test: `tests/unit/test_common.py`

- [ ] **Step 1: Criar config de teste e estrutura**

Create `tests/__init__.py` (vazio), `tests/unit/__init__.py` (vazio). Create `pytest.ini` na raiz do repo:

```ini
[pytest]
pythonpath = api
testpaths = tests
```

- [ ] **Step 2: Escrever o teste que falha**

Create `tests/unit/test_common.py`:

```python
import pytest
from app.common.errors import DomainError, NotFoundError, ValidationError, UnauthorizedError
from app.common.responses import success_payload, error_payload


def test_domain_error_default_status():
    assert DomainError("x").status == 400

def test_not_found_status():
    assert NotFoundError("nao achei").status == 404
    assert str(NotFoundError("nao achei")) == "nao achei"

def test_validation_error_carries_details():
    err = ValidationError("invalido", details={"name": ["obrigatorio"]})
    assert err.status == 422
    assert err.details == {"name": ["obrigatorio"]}

def test_unauthorized_status():
    assert UnauthorizedError("nope").status == 401

def test_success_payload_shape():
    body, status = success_payload("ok", {"id": 1})
    assert status == 200
    assert body == {"success": True, "message": "ok", "data": {"id": 1}}

def test_success_payload_custom_status():
    body, status = success_payload("criado", {"id": 1}, status=201)
    assert status == 201

def test_error_payload_shape():
    body, status = error_payload("falhou", status=404, errors={"x": ["y"]})
    assert status == 404
    assert body == {"success": False, "message": "falhou", "errors": {"x": ["y"]}}
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `pytest tests/unit/test_common.py -v`
Expected: FAIL (ModuleNotFoundError: app.common.errors)

- [ ] **Step 4: Implementar `errors.py`**

```python
class DomainError(Exception):
    status = 400

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        return self.message


class ValidationError(DomainError):
    status = 422


class UnauthorizedError(DomainError):
    status = 401


class NotFoundError(DomainError):
    status = 404


class ExternalServiceError(DomainError):
    status = 502
```

- [ ] **Step 5: Implementar `responses.py`**

```python
def success_payload(message: str = "Operação bem sucedida!", data=None, status: int = 200):
    return {"success": True, "message": message, "data": data}, status


def error_payload(message: str, status: int = 400, errors=None):
    return {"success": False, "message": message, "errors": errors}, status
```

- [ ] **Step 6: Implementar `decorators.py`**

```python
import logging
from functools import wraps

from flask import jsonify
from pydantic import ValidationError as PydanticValidationError

from app.common.errors import DomainError
from app.common.responses import error_payload
from app.extensions import db

logger = logging.getLogger(__name__)


def handle_errors(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except DomainError as exc:
            body, status = error_payload(exc.message, exc.status, exc.details)
            return jsonify(body), status
        except PydanticValidationError as exc:
            body, status = error_payload("Dados inválidos!", 422, _format_pydantic(exc))
            return jsonify(body), status
        except Exception as exc:  # noqa: BLE001
            logger.exception("Erro não tratado")
            db.session.rollback()
            body, status = error_payload("Erro interno do servidor!", 500)
            return jsonify(body), status

    return wrapper


def _format_pydantic(exc: PydanticValidationError) -> dict:
    errors: dict[str, list[str]] = {}
    for err in exc.errors():
        field = ".".join(str(p) for p in err["loc"]) or "_"
        errors.setdefault(field, []).append(err["msg"])
    return errors


def transactional(fn):
    @wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            result = fn(self, *args, **kwargs)
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise

    return wrapper
```

- [ ] **Step 7: Implementar `files.py`** (DRY de tamanho/leitura CSV usados em datasets e data mining)

```python
from io import BytesIO

import pandas as pd


def bytes_to_mb_label(num_bytes: int) -> str:
    return f"{round(num_bytes / (1024 * 1024), 4)}MB"


def read_csv(file_url: str) -> pd.DataFrame:
    return pd.read_csv(file_url)


def dataframe_to_csv_upload(df: pd.DataFrame, filename: str):
    buffer = BytesIO()
    df.to_csv(buffer, header=True, index=False)
    buffer.seek(0)
    size_label = bytes_to_mb_label(buffer.getbuffer().nbytes)
    upload = BytesIO(buffer.read())
    upload.filename = filename
    upload.content_type = "text/csv"
    return upload, size_label
```

- [ ] **Step 8: Rodar e ver passar**

Run: `pytest tests/unit/test_common.py -v`
Expected: PASS (7 passed)

- [ ] **Step 9: Commit**

```bash
git add tests/__init__.py tests/unit api/app/common pytest.ini
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: adiciona camada common (erros, respostas, decorators, helpers de arquivo)"
```

---

## Task 2: Infra de testes (conftest, app de teste, factories)

**Files:**
- Modify: `api/app/extensions.py` (remover `csrf` e `swagger` template global)
- Modify: `api/app/config.py` (adicionar `TestConfig`, remover flags CSRF)
- Create: `tests/conftest.py`
- Create: `tests/factories.py`
- Create: `tests/integration/__init__.py` (vazio)

> Nota: o `create_app()` ainda não aceita config customizada nesta etapa — será ajustado na Task 14. Para destravar testes agora, o conftest cria o app diretamente com uma app factory de teste mínima que importa as extensions e models. A app real de produção será religada na Task 14, quando os controllers novos existirem.

- [ ] **Step 1: Ajustar `config.py`** — substituir conteúdo por:

```python
import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret")
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
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    S3_BUCKET = "test-bucket"
    S3_KEY = "test-key"
    S3_SECRET = "test-secret"
    SESSION_COOKIE_SECURE = False
    LOGIN_DISABLED = False
    WTF_CSRF_ENABLED = False
```

- [ ] **Step 2: Ajustar `extensions.py`** — substituir conteúdo por:

```python
from flask_cors import CORS
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
cors = CORS()
```

- [ ] **Step 3: Criar `tests/conftest.py`**

```python
import boto3
import pytest
from moto import mock_aws

from app.config import TestConfig
from app.extensions import db as _db


@pytest.fixture()
def app():
    from app import create_app  # importado tarde: religado na Task 14
    application = create_app(TestConfig)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def db(app):
    return _db


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def s3(app):
    with mock_aws():
        conn = boto3.client(
            "s3",
            aws_access_key_id="test-key",
            aws_secret_access_key="test-secret",
            region_name="us-east-1",
        )
        conn.create_bucket(Bucket="test-bucket")
        yield conn


@pytest.fixture()
def auth_client(client, db):
    from app.models import User

    user = User(name="Usuario De Teste", phone_number="11999990000", email="user@test.com")
    user.set_password("senha1234")
    db.session.add(user)
    db.session.commit()
    client.post("/api/auth/login", json={"email": "user@test.com", "password": "senha1234"})
    return client, user
```

- [ ] **Step 4: Criar `tests/factories.py`** (helpers de criação de dados)

```python
from app.extensions import db
from app.models import Dataset, Project, User


def make_user(email="user@test.com", phone="11999990000", password="senha1234"):
    user = User(name="Usuario De Teste", phone_number=phone, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def make_project(user, name="Projeto Teste"):
    project = Project(name=name, description="descricao do projeto", user_id=user.id)
    db.session.add(project)
    db.session.commit()
    return project


def make_dataset(user, project, name="Base Teste", file_url="https://test-bucket.s3.amazonaws.com/abc.csv"):
    dataset = Dataset(
        name=name, description="descricao base", size_file="0.01MB",
        file_url=file_url, project_id=project.id, user_id=user.id,
    )
    db.session.add(dataset)
    db.session.commit()
    return dataset
```

- [ ] **Step 5: Verificar que conftest importa sem erro de sintaxe**

Run: `python -c "import ast; ast.parse(open('tests/conftest.py').read()); ast.parse(open('tests/factories.py').read()); print('ok')"`
Expected: `ok`

> Os testes ainda não rodam porque `create_app(TestConfig)` não aceita argumento até a Task 14. Isso é esperado; a fixture será exercitada a partir da Task 5 em diante conforme controllers existirem. Para destravar, a Task 14 é pré-requisito de execução dos testes de integração — mas escrevemos os testes antes (TDD) e os rodaremos após o wiring. **Para permitir TDD imediato nas Tasks 3–8, a Task 14 será parcialmente antecipada**: ver Step 6.

- [ ] **Step 6: Antecipar app factory mínima que aceita config**

Modify `api/app/__init__.py` — substituir a assinatura para aceitar config opcional (mantendo comportamento atual de produção temporariamente):

```python
def create_app(config_object=None):
    app = Flask(__name__)
    from app.config import Config
    app.config.from_object(config_object or Config)
    register_extensions(app)
    # blueprints antigos permanecem registrados até a Task 14
    register_blueprints(app)
    register_home_route(app)
    initialize_s3_controller(app)
    register_response_errors(app)
    return app
```

E em `register_extensions`, remover as linhas `csrf.init_app(app)` e `swagger.init_app(app)` e o import correspondente (já removidos de extensions.py). Remover também `login_manager` import se quebrar — manter `login_manager.init_app(app)`.

> Atenção: `register_response_errors` e `initialize_s3_controller` ainda referenciam código antigo. Mantenha-os por ora; serão removidos na Task 14. Se algum import quebrar a subida do app de teste, comente temporariamente a linha e anote no commit.

- [ ] **Step 7: Smoke test da fixture**

Create temporário `tests/integration/test_smoke.py`:

```python
def test_app_boots(client):
    resp = client.get("/")
    assert resp.status_code == 200
```

Run: `pytest tests/integration/test_smoke.py -v`
Expected: PASS. Depois delete o arquivo: `rm tests/integration/test_smoke.py`

- [ ] **Step 8: Commit**

```bash
git add api/app/extensions.py api/app/config.py api/app/__init__.py tests/conftest.py tests/factories.py tests/integration/__init__.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "test: adiciona infraestrutura de testes (conftest, factories, TestConfig) e remove CSRF/swagger global"
```

---

## Task 3: `StorageClient` (S3)

**Files:**
- Create: `api/app/storage/__init__.py` (vazio)
- Create: `api/app/storage/s3_client.py`
- Test: `tests/integration/test_storage.py`

- [ ] **Step 1: Escrever teste que falha**

Create `tests/integration/test_storage.py`:

```python
from io import BytesIO

from app.storage.s3_client import StorageClient


def test_upload_returns_url(app, s3):
    client = StorageClient(bucket="test-bucket", key="test-key", secret="test-secret")
    upload = BytesIO(b"a,b\n1,2\n")
    upload.filename = "file123.csv"
    upload.content_type = "text/csv"
    url = client.upload(upload)
    assert url == "https://test-bucket.s3.amazonaws.com/file123.csv"


def test_delete_returns_true(app, s3):
    client = StorageClient(bucket="test-bucket", key="test-key", secret="test-secret")
    upload = BytesIO(b"x")
    upload.filename = "todelete.csv"
    upload.content_type = "text/csv"
    client.upload(upload)
    assert client.delete("https://test-bucket.s3.amazonaws.com/todelete.csv") is True
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_storage.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implementar `s3_client.py`**

```python
import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.common.errors import ExternalServiceError


class StorageClient:
    def __init__(self, bucket: str, key: str, secret: str):
        self._bucket = bucket
        self._client = boto3.client(
            "s3", aws_access_key_id=key, aws_secret_access_key=secret
        )

    @staticmethod
    def _key_from_url(file_url: str) -> str:
        return file_url.split("/")[-1]

    def upload(self, file, acl: str = "public-read") -> str:
        try:
            self._client.upload_fileobj(
                file, self._bucket, file.filename,
                ExtraArgs={"ACL": acl, "ContentType": file.content_type},
            )
            return f"https://{self._bucket}.s3.amazonaws.com/{file.filename}"
        except (BotoCoreError, ClientError) as exc:
            raise ExternalServiceError("Erro ao realizar upload para o S3") from exc

    def delete(self, file_url: str) -> bool:
        if not file_url:
            return True
        try:
            self._client.delete_object(Bucket=self._bucket, Key=self._key_from_url(file_url))
            return True
        except (BotoCoreError, ClientError) as exc:
            raise ExternalServiceError("Erro ao deletar arquivo no S3") from exc
```

- [ ] **Step 4: Rodar e ver passar**

Run: `pytest tests/integration/test_storage.py -v`
Expected: PASS (2 passed)

- [ ] **Step 5: Commit**

```bash
git add api/app/storage tests/integration/test_storage.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: adiciona StorageClient encapsulando S3 com erros de domínio"
```

---

## Task 4: `BaseRepository` e repositórios

**Files:**
- Create: `api/app/repositories/__init__.py` (vazio)
- Create: `api/app/repositories/base.py`
- Create: `api/app/repositories/user_repository.py`
- Create: `api/app/repositories/project_repository.py`
- Create: `api/app/repositories/dataset_repository.py`
- Create: `api/app/repositories/clean_dataset_repository.py`
- Test: `tests/integration/test_repositories.py`

- [ ] **Step 1: Escrever teste que falha**

Create `tests/integration/test_repositories.py`:

```python
from app.repositories.user_repository import UserRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.dataset_repository import DatasetRepository
from tests.factories import make_user, make_project, make_dataset


def test_user_repo_get_by_email(app, db):
    user = make_user(email="a@test.com")
    repo = UserRepository(db.session)
    assert repo.get_by_email("a@test.com").id == user.id
    assert repo.get_by_email("missing@test.com") is None


def test_project_repo_list_by_user(app, db):
    user = make_user()
    make_project(user, name="P1")
    make_project(user, name="P2")
    repo = ProjectRepository(db.session)
    assert len(repo.list_by_user(user.id)) == 2


def test_dataset_repo_get_owned(app, db):
    user = make_user()
    project = make_project(user)
    ds = make_dataset(user, project)
    repo = DatasetRepository(db.session)
    assert repo.get_owned(ds.id, user.id).id == ds.id
    assert repo.get_owned(ds.id, user.id + 999) is None
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_repositories.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implementar `base.py`**

```python
class BaseRepository:
    model = None

    def __init__(self, session):
        self.session = session

    def get(self, entity_id):
        return self.session.get(self.model, entity_id)

    def add(self, entity):
        self.session.add(entity)
        self.session.flush()
        return entity

    def delete(self, entity):
        self.session.delete(entity)
```

> `add` usa `flush` (não `commit`) — o commit é responsabilidade do `@transactional` no service. Isso garante uma única transação por operação de negócio.

- [ ] **Step 4: Implementar `user_repository.py`**

```python
from app.models import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.session.query(User).filter_by(email=email).first()

    def email_taken(self, email: str, exclude_id: int | None = None) -> bool:
        query = self.session.query(User).filter(User.email == email)
        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)
        return self.session.query(query.exists()).scalar()

    def phone_taken(self, phone: str, exclude_id: int | None = None) -> bool:
        query = self.session.query(User).filter(User.phone_number == phone)
        if exclude_id is not None:
            query = query.filter(User.id != exclude_id)
        return self.session.query(query.exists()).scalar()
```

- [ ] **Step 5: Implementar `project_repository.py`**

```python
from app.models import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository):
    model = Project

    def list_by_user(self, user_id: int) -> list[Project]:
        return self.session.query(Project).filter_by(user_id=user_id).all()

    def get_owned(self, project_id: int, user_id: int) -> Project | None:
        return self.session.query(Project).filter_by(id=project_id, user_id=user_id).first()

    def name_taken(self, name: str, user_id: int, exclude_id: int | None = None) -> bool:
        query = self.session.query(Project).filter(Project.name == name, Project.user_id == user_id)
        if exclude_id is not None:
            query = query.filter(Project.id != exclude_id)
        return self.session.query(query.exists()).scalar()
```

- [ ] **Step 6: Implementar `dataset_repository.py`**

```python
from app.models import Dataset
from app.repositories.base import BaseRepository


class DatasetRepository(BaseRepository):
    model = Dataset

    def list_by_user(self, user_id: int) -> list[Dataset]:
        return self.session.query(Dataset).filter_by(user_id=user_id).all()

    def get_owned(self, dataset_id: int, user_id: int) -> Dataset | None:
        return self.session.query(Dataset).filter_by(id=dataset_id, user_id=user_id).first()

    def name_taken(self, name: str, user_id: int, exclude_id: int | None = None) -> bool:
        query = self.session.query(Dataset).filter(Dataset.name == name, Dataset.user_id == user_id)
        if exclude_id is not None:
            query = query.filter(Dataset.id != exclude_id)
        return self.session.query(query.exists()).scalar()
```

- [ ] **Step 7: Implementar `clean_dataset_repository.py`**

```python
from app.models import CleanDataset
from app.repositories.base import BaseRepository


class CleanDatasetRepository(BaseRepository):
    model = CleanDataset

    def get_by_dataset(self, dataset_id: int) -> CleanDataset | None:
        return self.session.query(CleanDataset).filter_by(dataset_id=dataset_id).first()
```

- [ ] **Step 8: Rodar e ver passar**

Run: `pytest tests/integration/test_repositories.py -v`
Expected: PASS (3 passed)

- [ ] **Step 9: Commit**

```bash
git add api/app/repositories tests/integration/test_repositories.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: adiciona repositories (base, user, project, dataset, clean_dataset)"
```

---

## Task 5: Domínio Auth

**Files:**
- Create: `api/app/schemas/__init__.py` (vazio), `api/app/schemas/auth.py`, `api/app/schemas/user.py`
- Create: `api/app/services/__init__.py` (vazio), `api/app/services/auth_service.py`
- Create: `api/app/controllers/__init__.py`, `api/app/controllers/auth_controller.py`
- Test: `tests/integration/test_auth.py`

> Endpoints: `POST /api/auth/login` (público), `POST /api/auth/logout` (login), `GET /api/auth/me` (login). O endpoint `/csrf-token` é REMOVIDO.

- [ ] **Step 1: Escrever testes que falham**

Create `tests/integration/test_auth.py`:

```python
from tests.factories import make_user


def test_login_success(client, db):
    make_user(email="a@test.com", password="senha1234")
    resp = client.post("/api/auth/login", json={"email": "a@test.com", "password": "senha1234"})
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["success"] is True
    assert body["data"]["email"] == "a@test.com"
    assert "password_hash" not in body["data"]


def test_login_invalid_credentials(client, db):
    make_user(email="a@test.com", password="senha1234")
    resp = client.post("/api/auth/login", json={"email": "a@test.com", "password": "errada"})
    assert resp.status_code == 401
    assert resp.get_json()["success"] is False


def test_login_invalid_payload(client, db):
    resp = client.post("/api/auth/login", json={"email": "naoemail"})
    assert resp.status_code == 422


def test_me_requires_login(client, db):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_returns_current_user(auth_client):
    client, user = auth_client
    resp = client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["email"] == user.email


def test_logout(auth_client):
    client, _ = auth_client
    resp = client.post("/api/auth/logout")
    assert resp.status_code == 200
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_auth.py -v`
Expected: FAIL (rotas antigas respondem formato diferente / import error)

- [ ] **Step 3: Implementar `schemas/user.py`** (read schema reusado por auth e users)

```python
from pydantic import BaseModel, ConfigDict


class UserReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    phone_number: str
    email: str
```

- [ ] **Step 4: Implementar `schemas/auth.py`**

```python
from pydantic import BaseModel, EmailStr, Field


class LoginSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)
```

- [ ] **Step 5: Implementar `services/auth_service.py`**

```python
from flask_login import login_user, logout_user

from app.common.errors import UnauthorizedError
from app.models import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginSchema


class AuthService:
    def __init__(self, users: UserRepository):
        self._users = users

    def login(self, data: LoginSchema) -> User:
        user = self._users.get_by_email(data.email)
        if not user or not user.check_password(data.password):
            raise UnauthorizedError("Credenciais inválidas!")
        login_user(user)
        return user

    def logout(self) -> None:
        logout_user()
```

- [ ] **Step 6: Implementar `controllers/auth_controller.py`**

```python
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.auth import LoginSchema
from app.schemas.user import UserReadSchema

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/login")
@handle_errors
def login():
    if current_user.is_authenticated:
        current_app.services["auth"].logout()
    data = LoginSchema.model_validate(request.get_json(silent=True) or {})
    user = current_app.services["auth"].login(data)
    body, status = success_payload("Login realizado com sucesso!", UserReadSchema.model_validate(user).model_dump())
    return jsonify(body), status


@auth_bp.post("/logout")
@login_required
@handle_errors
def logout():
    current_app.services["auth"].logout()
    body, status = success_payload("Logout realizado com sucesso!")
    return jsonify(body), status


@auth_bp.get("/me")
@login_required
@handle_errors
def me():
    body, status = success_payload(
        "Usuário atual recuperado com sucesso!",
        UserReadSchema.model_validate(current_user).model_dump(),
    )
    return jsonify(body), status
```

> `current_app.services` é o dict de serviços montado no wiring (Task 14). Para rodar estes testes ANTES da Task 14, execute a Task 14 Step de wiring primeiro OU registre os serviços num conftest. **Decisão:** a Task 14 (wiring + registro de blueprints novos) deve ser feita logo após a Task 5, então reordene se necessário. Para manter TDD verde aqui, o implementador deve aplicar o wiring mínimo da Task 14 (Steps 1–4) antes de rodar este teste. Isto está explicitado na Task 14.

- [ ] **Step 7: Aplicar wiring mínimo da Task 14 (ver Task 14 Steps 1–5) e rodar**

Run: `pytest tests/integration/test_auth.py -v`
Expected: PASS (6 passed)

- [ ] **Step 8: Commit**

```bash
git add api/app/schemas api/app/services/__init__.py api/app/services/auth_service.py api/app/controllers/__init__.py api/app/controllers/auth_controller.py tests/integration/test_auth.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: refatora domínio auth (schema/service/controller) com Pydantic"
```

---

## Task 6: Domínio Users

**Files:**
- Create: `api/app/schemas/user.py` (adicionar Create/Update aos já existentes)
- Create: `api/app/services/user_service.py`
- Create: `api/app/controllers/user_controller.py`
- Test: `tests/integration/test_users.py`

> Endpoints: `POST /api/users/` (público, cria), `PUT /api/users/` (login, atualiza o próprio), `DELETE /api/users/` (login, apaga o próprio + dados relacionados em cascade). Validações originais (UserForm): nome 10–150, telefone 11–20 único, email válido 6–200 único, senha 8–30.

- [ ] **Step 1: Escrever testes que falham**

Create `tests/integration/test_users.py`:

```python
from tests.factories import make_user


def test_create_user_success(client, db):
    payload = {"name": "Novo Usuario Teste", "phone_number": "11988887777",
               "email": "novo@test.com", "password": "senha1234"}
    resp = client.post("/api/users/", json=payload)
    assert resp.status_code == 201
    assert resp.get_json()["data"]["email"] == "novo@test.com"
    assert "password_hash" not in resp.get_json()["data"]


def test_create_user_duplicate_email(client, db):
    make_user(email="dup@test.com")
    payload = {"name": "Outro Usuario Teste", "phone_number": "11911112222",
               "email": "dup@test.com", "password": "senha1234"}
    resp = client.post("/api/users/", json=payload)
    assert resp.status_code == 422


def test_create_user_invalid(client, db):
    resp = client.post("/api/users/", json={"name": "x", "email": "bad", "phone_number": "1", "password": "1"})
    assert resp.status_code == 422


def test_update_user(auth_client):
    client, user = auth_client
    resp = client.put("/api/users/", json={"name": "Nome Atualizado Teste"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["name"] == "Nome Atualizado Teste"


def test_update_requires_login(client, db):
    resp = client.put("/api/users/", json={"name": "Nome Atualizado Teste"})
    assert resp.status_code == 401


def test_delete_user(auth_client):
    client, _ = auth_client
    resp = client.delete("/api/users/")
    assert resp.status_code == 200
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_users.py -v`
Expected: FAIL

- [ ] **Step 3: Adicionar schemas em `schemas/user.py`** (acrescentar ao arquivo existente):

```python
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    phone_number: str
    email: str


class UserCreateSchema(BaseModel):
    name: str = Field(min_length=10, max_length=150)
    phone_number: str = Field(min_length=11, max_length=20)
    email: EmailStr = Field(max_length=200)
    password: str = Field(min_length=8, max_length=30)


class UserUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=10, max_length=150)
    phone_number: str | None = Field(default=None, min_length=11, max_length=20)
    email: EmailStr | None = Field(default=None, max_length=200)
    password: str | None = Field(default=None, min_length=8, max_length=30)
```

- [ ] **Step 4: Implementar `services/user_service.py`**

```python
from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.models import User
from app.repositories.user_repository import UserRepository


class UserService:
    def __init__(self, users: UserRepository):
        self._users = users

    @transactional
    def create(self, data) -> User:
        self._ensure_unique(data.email, data.phone_number)
        user = User(name=data.name, phone_number=data.phone_number, email=data.email)
        user.set_password(data.password)
        return self._users.add(user)

    @transactional
    def update(self, user_id: int, data) -> User:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado!")
        if data.email and data.email != user.email:
            if self._users.email_taken(data.email, exclude_id=user_id):
                raise ValidationError("Dados inválidos!", {"email": ["E-mail já cadastrado."]})
            user.email = data.email
        if data.phone_number and data.phone_number != user.phone_number:
            if self._users.phone_taken(data.phone_number, exclude_id=user_id):
                raise ValidationError("Dados inválidos!", {"phone_number": ["Número de telefone já cadastrado."]})
            user.phone_number = data.phone_number
        if data.name:
            user.name = data.name
        if data.password:
            user.set_password(data.password)
        return user

    @transactional
    def delete(self, user_id: int) -> User:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado!")
        self._users.delete(user)
        return user

    def _ensure_unique(self, email: str, phone: str) -> None:
        errors = {}
        if self._users.email_taken(email):
            errors["email"] = ["E-mail já cadastrado."]
        if self._users.phone_taken(phone):
            errors["phone_number"] = ["Número de telefone já cadastrado."]
        if errors:
            raise ValidationError("Dados inválidos!", errors)
```

> Os datasets/projects/clean_datasets do usuário são apagados via `cascade="all, delete-orphan"` definido nos models. **Atenção:** os arquivos no S3 NÃO são apagados pelo cascade do banco. Para o delete de usuário, o service deve, antes de deletar, coletar as `file_url` dos datasets e clean_datasets e chamar `storage.delete` para cada uma. Adicione `storage: StorageClient` ao construtor e, em `delete`, itere `user.datasets` e `user.clean_datasets` removendo arquivos. Implemente assim:

```python
    def __init__(self, users: UserRepository, storage):
        self._users = users
        self._storage = storage

    @transactional
    def delete(self, user_id: int) -> User:
        user = self._users.get(user_id)
        if not user:
            raise NotFoundError("Usuário não encontrado!")
        for dataset in list(user.datasets):
            if dataset.file_url:
                self._storage.delete(dataset.file_url)
        for clean in list(user.clean_datasets):
            if clean.file_url:
                self._storage.delete(clean.file_url)
        self._users.delete(user)
        return user
```

- [ ] **Step 5: Implementar `controllers/user_controller.py`**

```python
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.user import UserCreateSchema, UserReadSchema, UserUpdateSchema

user_bp = Blueprint("users", __name__)


@user_bp.post("/")
@handle_errors
def create_user():
    data = UserCreateSchema.model_validate(request.get_json(silent=True) or {})
    user = current_app.services["user"].create(data)
    body, status = success_payload("Usuário criado com sucesso!", UserReadSchema.model_validate(user).model_dump(), status=201)
    return jsonify(body), status


@user_bp.put("/")
@login_required
@handle_errors
def update_user():
    data = UserUpdateSchema.model_validate(request.get_json(silent=True) or {})
    user = current_app.services["user"].update(current_user.id, data)
    body, status = success_payload("Usuário atualizado com sucesso!", UserReadSchema.model_validate(user).model_dump())
    return jsonify(body), status


@user_bp.delete("/")
@login_required
@handle_errors
def delete_user():
    user = current_app.services["user"].delete(current_user.id)
    body, status = success_payload("Usuário deletado com sucesso!", UserReadSchema.model_validate(user).model_dump())
    return jsonify(body), status
```

- [ ] **Step 6: Registrar blueprint no wiring (Task 14) e rodar**

Run: `pytest tests/integration/test_users.py -v`
Expected: PASS (6 passed)

- [ ] **Step 7: Commit**

```bash
git add api/app/schemas/user.py api/app/services/user_service.py api/app/controllers/user_controller.py tests/integration/test_users.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: refatora domínio users (schema/service/controller) com Pydantic"
```

---

## Task 7: Domínio Projects

**Files:**
- Create: `api/app/schemas/project.py`
- Create: `api/app/services/project_service.py`
- Create: `api/app/controllers/project_controller.py`
- Test: `tests/integration/test_projects.py`

> Endpoints: list/get/create/update/delete (todos login). Validações originais: nome 2–100 único por usuário, descrição opcional 10–2000. GET de um projeto inclui lista de datasets. Delete remove datasets em cascade (apagar arquivos S3 como no user service).

- [ ] **Step 1: Escrever testes que falham**

Create `tests/integration/test_projects.py`:

```python
from tests.factories import make_project, make_dataset


def test_list_projects(auth_client):
    client, user = auth_client
    make_project(user, name="Projeto Um")
    make_project(user, name="Projeto Dois")
    resp = client.get("/api/projects/")
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 2


def test_get_project_with_datasets(auth_client):
    client, user = auth_client
    project = make_project(user)
    make_dataset(user, project)
    resp = client.get(f"/api/projects/{project.id}")
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]["datasets"]) == 1


def test_get_project_not_found(auth_client):
    client, _ = auth_client
    resp = client.get("/api/projects/9999")
    assert resp.status_code == 404


def test_create_project(auth_client):
    client, _ = auth_client
    resp = client.post("/api/projects/", json={"name": "Novo Projeto", "description": "uma descricao valida"})
    assert resp.status_code == 201
    assert resp.get_json()["data"]["name"] == "Novo Projeto"


def test_create_duplicate_name(auth_client):
    client, user = auth_client
    make_project(user, name="Repetido")
    resp = client.post("/api/projects/", json={"name": "Repetido"})
    assert resp.status_code == 422


def test_update_project(auth_client):
    client, user = auth_client
    project = make_project(user)
    resp = client.put(f"/api/projects/{project.id}", json={"name": "Nome Novo"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["name"] == "Nome Novo"


def test_delete_project(auth_client):
    client, user = auth_client
    project = make_project(user)
    resp = client.delete(f"/api/projects/{project.id}")
    assert resp.status_code == 200


def test_requires_login(client, db):
    assert client.get("/api/projects/").status_code == 401
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_projects.py -v`
Expected: FAIL

- [ ] **Step 3: Implementar `schemas/project.py`**

```python
from pydantic import BaseModel, ConfigDict, Field


class ProjectCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=2000)


class ProjectUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=2000)


class DatasetSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    size_file: str
    file_url: str | None


class ProjectReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None


class ProjectDetailSchema(ProjectReadSchema):
    datasets: list[DatasetSummarySchema] = []
```

- [ ] **Step 4: Implementar `services/project_service.py`**

```python
from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.models import Project
from app.repositories.project_repository import ProjectRepository


class ProjectService:
    def __init__(self, projects: ProjectRepository, storage):
        self._projects = projects
        self._storage = storage

    def list(self, user_id: int) -> list[Project]:
        return self._projects.list_by_user(user_id)

    def get(self, project_id: int, user_id: int) -> Project:
        project = self._projects.get_owned(project_id, user_id)
        if not project:
            raise NotFoundError("Projeto não encontrado!")
        return project

    @transactional
    def create(self, data, user_id: int) -> Project:
        if self._projects.name_taken(data.name, user_id):
            raise ValidationError("Dados inválidos!", {"name": ["O nome do projeto já existe."]})
        return self._projects.add(Project(name=data.name, description=data.description, user_id=user_id))

    @transactional
    def update(self, project_id: int, data, user_id: int) -> Project:
        project = self.get(project_id, user_id)
        if data.name and data.name != project.name:
            if self._projects.name_taken(data.name, user_id, exclude_id=project_id):
                raise ValidationError("Dados inválidos!", {"name": ["O nome do projeto já existe."]})
            project.name = data.name
        if data.description:
            project.description = data.description
        return project

    @transactional
    def delete(self, project_id: int, user_id: int) -> Project:
        project = self.get(project_id, user_id)
        for dataset in list(project.datasets):
            if dataset.file_url:
                self._storage.delete(dataset.file_url)
            if dataset.clean_dataset and dataset.clean_dataset.file_url:
                self._storage.delete(dataset.clean_dataset.file_url)
        self._projects.delete(project)
        return project
```

- [ ] **Step 5: Implementar `controllers/project_controller.py`**

```python
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.project import ProjectCreateSchema, ProjectDetailSchema, ProjectReadSchema, ProjectUpdateSchema

project_bp = Blueprint("projects", __name__)


@project_bp.get("/")
@login_required
@handle_errors
def list_projects():
    projects = current_app.services["project"].list(current_user.id)
    data = [ProjectReadSchema.model_validate(p).model_dump() for p in projects]
    body, status = success_payload("Projetos recuperados com sucesso!", data)
    return jsonify(body), status


@project_bp.get("/<int:project_id>")
@login_required
@handle_errors
def get_project(project_id):
    project = current_app.services["project"].get(project_id, current_user.id)
    body, status = success_payload("Projeto recuperado com sucesso!", ProjectDetailSchema.model_validate(project).model_dump())
    return jsonify(body), status


@project_bp.post("/")
@login_required
@handle_errors
def create_project():
    data = ProjectCreateSchema.model_validate(request.get_json(silent=True) or {})
    project = current_app.services["project"].create(data, current_user.id)
    body, status = success_payload("Projeto criado com sucesso!", ProjectReadSchema.model_validate(project).model_dump(), status=201)
    return jsonify(body), status


@project_bp.put("/<int:project_id>")
@login_required
@handle_errors
def update_project(project_id):
    data = ProjectUpdateSchema.model_validate(request.get_json(silent=True) or {})
    project = current_app.services["project"].update(project_id, data, current_user.id)
    body, status = success_payload("Projeto atualizado com sucesso!", ProjectReadSchema.model_validate(project).model_dump())
    return jsonify(body), status


@project_bp.delete("/<int:project_id>")
@login_required
@handle_errors
def delete_project(project_id):
    project = current_app.services["project"].delete(project_id, current_user.id)
    body, status = success_payload("Projeto deletado com sucesso!", ProjectReadSchema.model_validate(project).model_dump())
    return jsonify(body), status
```

- [ ] **Step 6: Registrar blueprint no wiring (Task 14) e rodar**

Run: `pytest tests/integration/test_projects.py -v`
Expected: PASS (8 passed)

- [ ] **Step 7: Commit**

```bash
git add api/app/schemas/project.py api/app/services/project_service.py api/app/controllers/project_controller.py tests/integration/test_projects.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: refatora domínio projects (schema/service/controller) com Pydantic"
```

---

## Task 8: Domínio Datasets

**Files:**
- Create: `api/app/schemas/dataset.py`
- Create: `api/app/services/dataset_service.py`
- Create: `api/app/controllers/dataset_controller.py`
- Test: `tests/integration/test_datasets.py`

> Endpoints: list/get (login), `POST /create-dataset` (login, multipart com `csv_file`), `PUT /<id>` (login, multipart opcional), `DELETE /<id>` (login). Create exige: name 2–100 único por usuário, description opcional 10–2000, project_id existente e do usuário, csv_file (.csv, ≤16MB). O nome do arquivo no S3 é `md5(f"{user_id}_{name}").hexdigest() + ".csv"`. O GET de um dataset inclui `clean_dataset` se existir.

> **Validação de arquivo + multipart:** Pydantic não valida `FileStorage` diretamente. O controller extrai `request.form` e `request.files`, monta um dict e passa ao schema (campos texto), e passa o `FileStorage` separadamente ao service, que valida extensão/tamanho via helper. Implemente conforme abaixo.

- [ ] **Step 1: Escrever testes que falham**

Create `tests/integration/test_datasets.py`:

```python
import io

from tests.factories import make_project, make_dataset


def _csv_file():
    return (io.BytesIO(b"a,b\n1,2\n3,4\n"), "data.csv")


def test_list_datasets(auth_client):
    client, user = auth_client
    project = make_project(user)
    make_dataset(user, project, name="Base Um")
    resp = client.get("/api/datasets/")
    assert resp.status_code == 200
    assert len(resp.get_json()["data"]) == 1


def test_get_dataset(auth_client):
    client, user = auth_client
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.get(f"/api/datasets/{ds.id}")
    assert resp.status_code == 200
    assert resp.get_json()["data"]["id"] == ds.id


def test_get_dataset_not_found(auth_client):
    client, _ = auth_client
    assert client.get("/api/datasets/9999").status_code == 404


def test_create_dataset(auth_client, s3):
    client, user = auth_client
    project = make_project(user)
    data = {"name": "Nova Base", "description": "descricao valida aqui", "project_id": str(project.id),
            "csv_file": _csv_file()}
    resp = client.post("/api/datasets/create-dataset", data=data, content_type="multipart/form-data")
    assert resp.status_code == 201
    assert resp.get_json()["data"]["name"] == "Nova Base"


def test_create_dataset_invalid_project(auth_client, s3):
    client, _ = auth_client
    data = {"name": "Nova Base", "project_id": "9999", "csv_file": _csv_file()}
    resp = client.post("/api/datasets/create-dataset", data=data, content_type="multipart/form-data")
    assert resp.status_code in (404, 422)


def test_delete_dataset(auth_client, s3):
    client, user = auth_client
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.delete(f"/api/datasets/{ds.id}")
    assert resp.status_code == 200


def test_requires_login(client, db):
    assert client.get("/api/datasets/").status_code == 401
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_datasets.py -v`
Expected: FAIL

- [ ] **Step 3: Implementar `schemas/dataset.py`**

```python
from pydantic import BaseModel, ConfigDict, Field


class DatasetCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    project_id: int


class DatasetUpdateSchema(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, min_length=10, max_length=2000)
    project_id: int | None = None


class CleanDatasetReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    size_file: str
    file_url: str


class DatasetReadSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str | None
    size_file: str
    file_url: str | None
    project_id: int
    clean_dataset: CleanDatasetReadSchema | None = None
```

- [ ] **Step 4: Implementar `services/dataset_service.py`**

```python
import hashlib

from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.common.files import bytes_to_mb_label
from app.config import Config
from app.models import Dataset
from app.repositories.dataset_repository import DatasetRepository
from app.repositories.project_repository import ProjectRepository


class DatasetService:
    def __init__(self, datasets: DatasetRepository, projects: ProjectRepository, storage):
        self._datasets = datasets
        self._projects = projects
        self._storage = storage

    def list(self, user_id: int) -> list[Dataset]:
        return self._datasets.list_by_user(user_id)

    def get(self, dataset_id: int, user_id: int) -> Dataset:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")
        return dataset

    @transactional
    def create(self, data, csv_file, user_id: int) -> Dataset:
        self._validate_file(csv_file)
        if self._datasets.name_taken(data.name, user_id):
            raise ValidationError("Dados inválidos!", {"name": ["O nome da base de dados já existe."]})
        project = self._projects.get_owned(data.project_id, user_id)
        if not project:
            raise ValidationError("Dados inválidos!", {"project_id": ["O projeto não existe."]})
        size_label, file_url = self._store(csv_file, user_id, data.name)
        return self._datasets.add(Dataset(
            name=data.name, description=data.description, size_file=size_label,
            file_url=file_url, project_id=data.project_id, user_id=user_id,
        ))

    @transactional
    def update(self, dataset_id: int, data, csv_file, user_id: int) -> Dataset:
        dataset = self.get(dataset_id, user_id)
        if csv_file:
            self._validate_file(csv_file)
            size_label, file_url = self._store(csv_file, user_id, data.name or dataset.name)
            dataset.size_file = size_label
            dataset.file_url = file_url
        if data.name:
            dataset.name = data.name
        if data.description:
            dataset.description = data.description
        if data.project_id:
            dataset.project_id = data.project_id
        return dataset

    @transactional
    def delete(self, dataset_id: int, user_id: int) -> Dataset:
        dataset = self.get(dataset_id, user_id)
        if dataset.clean_dataset and dataset.clean_dataset.file_url:
            self._storage.delete(dataset.clean_dataset.file_url)
        if dataset.file_url:
            self._storage.delete(dataset.file_url)
        self._datasets.delete(dataset)
        return dataset

    def _store(self, csv_file, user_id: int, name: str) -> tuple[str, str]:
        csv_file.seek(0, 2)
        size_label = bytes_to_mb_label(csv_file.tell())
        csv_file.seek(0)
        file_hash = hashlib.md5(f"{user_id}_{name}".encode()).hexdigest()
        csv_file.filename = f"{file_hash}.csv"
        url = self._storage.upload(csv_file)
        return size_label, url

    @staticmethod
    def _validate_file(csv_file) -> None:
        if not csv_file.filename.lower().endswith(".csv"):
            raise ValidationError("Dados inválidos!", {"csv_file": ["Apenas arquivos CSV são permitidos."]})
        csv_file.seek(0, 2)
        size = csv_file.tell()
        csv_file.seek(0)
        if size > Config.MAX_CONTENT_LENGTH:
            raise ValidationError("Dados inválidos!", {"csv_file": ["O arquivo excede o tamanho máximo permitido"]})
```

- [ ] **Step 5: Implementar `controllers/dataset_controller.py`**

```python
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.errors import ValidationError
from app.common.responses import success_payload
from app.schemas.dataset import DatasetCreateSchema, DatasetReadSchema, DatasetUpdateSchema

dataset_bp = Blueprint("datasets", __name__)


@dataset_bp.get("/")
@login_required
@handle_errors
def list_datasets():
    datasets = current_app.services["dataset"].list(current_user.id)
    data = [DatasetReadSchema.model_validate(d).model_dump() for d in datasets]
    body, status = success_payload("Bases de dados recuperadas com sucesso!", data)
    return jsonify(body), status


@dataset_bp.get("/<int:dataset_id>")
@login_required
@handle_errors
def get_dataset(dataset_id):
    dataset = current_app.services["dataset"].get(dataset_id, current_user.id)
    body, status = success_payload("Base de dados recuperada com sucesso!", DatasetReadSchema.model_validate(dataset).model_dump())
    return jsonify(body), status


@dataset_bp.post("/create-dataset")
@login_required
@handle_errors
def create_dataset():
    csv_file = request.files.get("csv_file")
    if not csv_file:
        raise ValidationError("Dados inválidos!", {"csv_file": ["O campo é obrigatório."]})
    data = DatasetCreateSchema.model_validate(request.form.to_dict())
    dataset = current_app.services["dataset"].create(data, csv_file, current_user.id)
    body, status = success_payload("Base de dados criada com sucesso!", DatasetReadSchema.model_validate(dataset).model_dump(), status=201)
    return jsonify(body), status


@dataset_bp.put("/<int:dataset_id>")
@login_required
@handle_errors
def update_dataset(dataset_id):
    data = DatasetUpdateSchema.model_validate(request.form.to_dict())
    csv_file = request.files.get("csv_file")
    dataset = current_app.services["dataset"].update(dataset_id, data, csv_file, current_user.id)
    body, status = success_payload("Base de dados atualizada com sucesso!", DatasetReadSchema.model_validate(dataset).model_dump())
    return jsonify(body), status


@dataset_bp.delete("/<int:dataset_id>")
@login_required
@handle_errors
def delete_dataset(dataset_id):
    dataset = current_app.services["dataset"].delete(dataset_id, current_user.id)
    body, status = success_payload("Base de dados deletada com sucesso!", DatasetReadSchema.model_validate(dataset).model_dump())
    return jsonify(body), status
```

- [ ] **Step 6: Registrar blueprint no wiring (Task 14) e rodar**

Run: `pytest tests/integration/test_datasets.py -v`
Expected: PASS (7 passed)

- [ ] **Step 7: Commit**

```bash
git add api/app/schemas/dataset.py api/app/services/dataset_service.py api/app/controllers/dataset_controller.py tests/integration/test_datasets.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: refatora domínio datasets (schema/service/controller) com Pydantic"
```

---

## Task 9: Data Mining — Cleaning (Strategy)

**Files:**
- Create: `api/app/data_mining/__init__.py` (vazio), `api/app/data_mining/cleaning/__init__.py` (vazio), `api/app/data_mining/cleaning/strategies.py`
- Create: `api/app/schemas/data_mining/__init__.py` (vazio), `api/app/schemas/data_mining/cleaning.py`
- Create: `api/app/services/data_mining/__init__.py` (vazio), `api/app/services/data_mining/cleaning_service.py`
- Create: `api/app/controllers/data_mining/__init__.py` (vazio), `api/app/controllers/data_mining/preprocessing_controller.py`
- Test: `tests/integration/test_cleaning.py`

> Endpoint: `POST /api/preprocessing/data-cleaning/<int:dataset_id>` (login). Recebe JSON: `features` (lista de colunas), `methods` (uma de: media/mediana/moda), `missing_values` (lista de: null/""/?/0). Lê o CSV original do dataset, preenche valores ausentes nas features escolhidas com a estratégia, salva CSV limpo no S3, cria/substitui `CleanDataset`. Resposta: `{"clean_dataset": {id, size_file, file_url}}`.

- [ ] **Step 1: Escrever testes que falham**

Create `tests/integration/test_cleaning.py`:

```python
import pandas as pd

from app.data_mining.cleaning.strategies import get_strategy, MeanFillStrategy


def test_mean_strategy_fills_na():
    s = pd.Series([1.0, None, 3.0])
    result = MeanFillStrategy().apply(s)
    assert result.isna().sum() == 0
    assert round(result.iloc[1], 1) == 2.0


def test_get_strategy_unknown():
    import pytest
    from app.common.errors import ValidationError
    with pytest.raises(ValidationError):
        get_strategy("inexistente")


def test_data_cleaning_endpoint(auth_client, s3, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    from app.services.data_mining import cleaning_service as mod
    # CSV com valor ausente
    df = pd.DataFrame({"idade": [10, 0, 30], "peso": [50, 60, 70]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    payload = {"features": ["idade"], "methods": "media", "missing_values": ["0"]}
    resp = client.post(f"/api/preprocessing/data-cleaning/{ds.id}", json=payload)
    assert resp.status_code == 200
    assert "clean_dataset" in resp.get_json()["data"]
```

> Nota: `read_csv` é importado de `app.common.files` para dentro do módulo do service, permitindo monkeypatch sem acessar a internet/S3 real.

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_cleaning.py -v`
Expected: FAIL (ModuleNotFoundError)

- [ ] **Step 3: Implementar `data_mining/cleaning/strategies.py`**

```python
from abc import ABC, abstractmethod

import pandas as pd

from app.common.errors import ValidationError


class MissingValueStrategy(ABC):
    name: str

    @abstractmethod
    def apply(self, series: pd.Series) -> pd.Series: ...


class MeanFillStrategy(MissingValueStrategy):
    name = "media"

    def apply(self, series: pd.Series) -> pd.Series:
        return series.fillna(series.mean().round(4))


class MedianFillStrategy(MissingValueStrategy):
    name = "mediana"

    def apply(self, series: pd.Series) -> pd.Series:
        return series.fillna(series.median().round(4))


class ModeFillStrategy(MissingValueStrategy):
    name = "moda"

    def apply(self, series: pd.Series) -> pd.Series:
        return series.fillna(series.mode()[0])


_REGISTRY = {s.name: s for s in (MeanFillStrategy, MedianFillStrategy, ModeFillStrategy)}


def get_strategy(name: str) -> MissingValueStrategy:
    strategy = _REGISTRY.get(name)
    if strategy is None:
        raise ValidationError("Dados inválidos!", {"methods": [f"Opção inválida: {name}."]})
    return strategy()
```

- [ ] **Step 4: Implementar `schemas/data_mining/cleaning.py`**

```python
from pydantic import BaseModel, Field


class DataCleaningSchema(BaseModel):
    features: list[str] = Field(min_length=1)
    methods: str
    missing_values: list[str] = Field(min_length=1, max_length=4)
```

- [ ] **Step 5: Implementar `services/data_mining/cleaning_service.py`**

```python
import pandas as pd

from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.common.files import dataframe_to_csv_upload, read_csv
from app.data_mining.cleaning.strategies import get_strategy
from app.models import CleanDataset
from app.repositories.clean_dataset_repository import CleanDatasetRepository
from app.repositories.dataset_repository import DatasetRepository

_MISSING_MAP = {"null": None, "0": 0, "?": "?", "": None}


class DataCleaningService:
    def __init__(self, datasets: DatasetRepository, clean_datasets: CleanDatasetRepository, storage):
        self._datasets = datasets
        self._clean = clean_datasets
        self._storage = storage

    @transactional
    def clean(self, dataset_id: int, data, user_id: int) -> CleanDataset:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")

        df_original = read_csv(dataset.file_url)
        self._validate_features(df_original, data.features)
        df_clean = self._apply(df_original, data)

        filename = f"{dataset.file_url.split('/')[-1].split('.')[0]}_clean.csv"
        upload, size_label = dataframe_to_csv_upload(df_clean, filename)
        file_url = self._storage.upload(upload)

        existing = self._clean.get_by_dataset(dataset.id)
        if existing:
            if existing.file_url:
                self._storage.delete(existing.file_url)
            self._clean.delete(existing)

        return self._clean.add(CleanDataset(
            size_file=size_label, file_url=file_url, dataset_id=dataset.id, user_id=user_id,
        ))

    def _apply(self, df, data):
        missing = [_MISSING_MAP.get(v, v) for v in data.missing_values]
        strategy = get_strategy(data.methods)
        result = df.copy()
        for column in data.features:
            result[column] = result[column].replace(missing, pd.NA)
            result[column] = strategy.apply(pd.to_numeric(result[column], errors="coerce"))
        return result

    @staticmethod
    def _validate_features(df, features):
        invalid = [f for f in features if f not in df.columns]
        if invalid:
            raise ValidationError("Dados inválidos!", {"features": [f"Campos não registrados: {', '.join(invalid)}"]})
```

- [ ] **Step 6: Implementar `controllers/data_mining/preprocessing_controller.py`** (começa só com cleaning; normalization e reduction serão acrescentados nas Tasks 10–11)

```python
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.data_mining.cleaning import DataCleaningSchema

preprocessing_bp = Blueprint("preprocessing", __name__)


@preprocessing_bp.post("/data-cleaning/<int:dataset_id>")
@login_required
@handle_errors
def data_cleaning(dataset_id):
    data = DataCleaningSchema.model_validate(request.get_json(silent=True) or {})
    clean = current_app.services["cleaning"].clean(dataset_id, data, current_user.id)
    payload = {"clean_dataset": {"id": clean.id, "size_file": clean.size_file, "file_url": clean.file_url}}
    body, status = success_payload("Limpeza de dados realizada com sucesso!", payload)
    return jsonify(body), status
```

- [ ] **Step 7: Registrar serviço/blueprint no wiring (Task 14) e rodar**

Run: `pytest tests/integration/test_cleaning.py -v`
Expected: PASS (3 passed)

- [ ] **Step 8: Commit**

```bash
git add api/app/data_mining/__init__.py api/app/data_mining/cleaning api/app/schemas/data_mining api/app/services/data_mining/__init__.py api/app/services/data_mining/cleaning_service.py api/app/controllers/data_mining tests/integration/test_cleaning.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: refatora data cleaning com strategy pattern"
```

---

## Task 10: Data Mining — Normalization (Strategy)

**Files:**
- Create: `api/app/data_mining/normalization/__init__.py` (vazio), `api/app/data_mining/normalization/strategies.py`
- Create: `api/app/schemas/data_mining/normalization.py`
- Create: `api/app/services/data_mining/normalization_service.py`
- Modify: `api/app/controllers/data_mining/preprocessing_controller.py` (adicionar rota)
- Test: `tests/integration/test_normalization.py`

> Endpoint: `POST /api/preprocessing/data-normalization/<int:dataset_id>` (login). JSON: `features` (lista), `methods` (minmax|zscore). Normaliza colunas. Se já existe clean_dataset, normaliza sobre o arquivo limpo; senão sobre o original. Substitui o clean_dataset. Resposta: `{"normalized_dataset": {id, size_file, file_url}}`.

- [ ] **Step 1: Escrever testes que falham**

Create `tests/integration/test_normalization.py`:

```python
import pandas as pd

from app.data_mining.normalization.strategies import get_strategy, MinMaxStrategy


def test_minmax_scales_0_1():
    s = pd.Series([0.0, 5.0, 10.0])
    result = MinMaxStrategy().apply(s)
    assert round(result.min(), 4) == 0.0
    assert round(result.max(), 4) == 1.0


def test_get_strategy_unknown():
    import pytest
    from app.common.errors import ValidationError
    with pytest.raises(ValidationError):
        get_strategy("xpto")


def test_normalization_endpoint(auth_client, s3, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    from app.services.data_mining import normalization_service as mod
    df = pd.DataFrame({"idade": [10.0, 20.0, 30.0]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.post(f"/api/preprocessing/data-normalization/{ds.id}",
                       json={"features": ["idade"], "methods": "minmax"})
    assert resp.status_code == 200
    assert "normalized_dataset" in resp.get_json()["data"]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_normalization.py -v`
Expected: FAIL

- [ ] **Step 3: Implementar `data_mining/normalization/strategies.py`**

```python
from abc import ABC, abstractmethod

import pandas as pd
from sklearn.preprocessing import MinMaxScaler, StandardScaler

from app.common.errors import ValidationError


class NormalizationStrategy(ABC):
    name: str

    def apply(self, series: pd.Series) -> pd.Series:
        scaled = self._scaler().fit_transform(series.values.reshape(-1, 1))
        return pd.Series(scaled.flatten(), index=series.index).round(4)

    @abstractmethod
    def _scaler(self): ...


class MinMaxStrategy(NormalizationStrategy):
    name = "minmax"

    def _scaler(self):
        return MinMaxScaler()


class ZScoreStrategy(NormalizationStrategy):
    name = "zscore"

    def _scaler(self):
        return StandardScaler()


_REGISTRY = {s.name: s for s in (MinMaxStrategy, ZScoreStrategy)}


def get_strategy(name: str) -> NormalizationStrategy:
    strategy = _REGISTRY.get(name)
    if strategy is None:
        raise ValidationError("Dados inválidos!", {"methods": [f"Método inválido: {name}."]})
    return strategy()
```

- [ ] **Step 4: Implementar `schemas/data_mining/normalization.py`**

```python
from pydantic import BaseModel, Field


class DataNormalizationSchema(BaseModel):
    features: list[str] = Field(min_length=1)
    methods: str
```

- [ ] **Step 5: Implementar `services/data_mining/normalization_service.py`**

```python
from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.common.files import dataframe_to_csv_upload, read_csv
from app.data_mining.normalization.strategies import get_strategy
from app.models import CleanDataset
from app.repositories.clean_dataset_repository import CleanDatasetRepository
from app.repositories.dataset_repository import DatasetRepository


class DataNormalizationService:
    def __init__(self, datasets: DatasetRepository, clean_datasets: CleanDatasetRepository, storage):
        self._datasets = datasets
        self._clean = clean_datasets
        self._storage = storage

    @transactional
    def normalize(self, dataset_id: int, data, user_id: int) -> CleanDataset:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")

        existing = self._clean.get_by_dataset(dataset.id)
        source_url = existing.file_url if existing else dataset.file_url

        df = read_csv(source_url)
        invalid = [f for f in data.features if f not in df.columns]
        if invalid:
            raise ValidationError("Dados inválidos!", {"features": [f"Campos não registrados: {', '.join(invalid)}"]})

        strategy = get_strategy(data.methods)
        for feature in data.features:
            df[feature] = strategy.apply(df[feature])

        base_name = dataset.file_url.split("/")[-1].split(".")[0].split("_")[0]
        upload, size_label = dataframe_to_csv_upload(df, f"{base_name}_normalized.csv")
        file_url = self._storage.upload(upload)

        if existing:
            if existing.file_url:
                self._storage.delete(existing.file_url)
            self._clean.delete(existing)

        return self._clean.add(CleanDataset(
            size_file=size_label, file_url=file_url, dataset_id=dataset.id, user_id=user_id,
        ))
```

- [ ] **Step 6: Adicionar rota em `preprocessing_controller.py`**

```python
from app.schemas.data_mining.normalization import DataNormalizationSchema


@preprocessing_bp.post("/data-normalization/<int:dataset_id>")
@login_required
@handle_errors
def data_normalization(dataset_id):
    data = DataNormalizationSchema.model_validate(request.get_json(silent=True) or {})
    clean = current_app.services["normalization"].normalize(dataset_id, data, current_user.id)
    payload = {"normalized_dataset": {"id": clean.id, "size_file": clean.size_file, "file_url": clean.file_url}}
    body, status = success_payload("Normalização de dados realizada com sucesso!", payload)
    return jsonify(body), status
```

- [ ] **Step 7: Registrar serviço no wiring (Task 14) e rodar**

Run: `pytest tests/integration/test_normalization.py -v`
Expected: PASS (3 passed)

- [ ] **Step 8: Commit**

```bash
git add api/app/data_mining/normalization api/app/schemas/data_mining/normalization.py api/app/services/data_mining/normalization_service.py api/app/controllers/data_mining/preprocessing_controller.py tests/integration/test_normalization.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: refatora data normalization com strategy pattern"
```

---

## Task 11: Data Mining — Reduction (Strategy)

**Files:**
- Create: `api/app/data_mining/reduction/__init__.py` (vazio), `api/app/data_mining/reduction/strategies.py`
- Create: `api/app/schemas/data_mining/reduction.py`
- Create: `api/app/services/data_mining/reduction_service.py`
- Modify: `api/app/controllers/data_mining/preprocessing_controller.py` (adicionar rota)
- Test: `tests/integration/test_reduction.py`

> Endpoint: `POST /api/preprocessing/data-reduction/<int:dataset_id>` (login). JSON: `features` (lista), `methods` (pca|amostragem_aleatoria|amostragem_sistematica), e conforme método: `target` (obrigatório para pca, coluna existente), `random_records` (int, para aleatoria), `systematic_records` + `systematic_method` (maiores|menores) (para sistematica, exige exatamente 1 feature). Substitui clean_dataset. Resposta: `{"reduced_dataset": {id, size_file, file_url}}`.

- [ ] **Step 1: Escrever testes que falham**

Create `tests/integration/test_reduction.py`:

```python
import pandas as pd

from app.data_mining.reduction.strategies import RandomSamplingStrategy


def test_random_sampling_returns_n_rows():
    df = pd.DataFrame({"a": range(10), "b": range(10)})
    result = RandomSamplingStrategy().reduce(df, features=["a"], params={"random_records": 3})
    assert len(result) == 3


def test_reduction_endpoint_random(auth_client, s3, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    from app.services.data_mining import reduction_service as mod
    df = pd.DataFrame({"idade": range(10), "peso": range(10)})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.post(f"/api/preprocessing/data-reduction/{ds.id}",
                       json={"features": ["idade"], "methods": "amostragem_aleatoria", "random_records": 5})
    assert resp.status_code == 200
    assert "reduced_dataset" in resp.get_json()["data"]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_reduction.py -v`
Expected: FAIL

- [ ] **Step 3: Implementar `data_mining/reduction/strategies.py`**

```python
from abc import ABC, abstractmethod

import pandas as pd
from sklearn.decomposition import PCA

from app.common.errors import ValidationError


class ReductionStrategy(ABC):
    name: str

    @abstractmethod
    def reduce(self, df: pd.DataFrame, features: list[str], params: dict) -> pd.DataFrame: ...


class PCAStrategy(ReductionStrategy):
    name = "pca"

    def reduce(self, df, features, params):
        target = params.get("target")
        if not target or target not in df.columns:
            raise ValidationError("Dados inválidos!", {"target": [f"A coluna target '{target}' não está registrada."]})
        result = pd.DataFrame(PCA(n_components=2).fit_transform(df[features]), columns=["PC1", "PC2"])
        result[target] = df[target].values
        return result


class RandomSamplingStrategy(ReductionStrategy):
    name = "amostragem_aleatoria"

    def reduce(self, df, features, params):
        n = params.get("random_records")
        if not n:
            raise ValidationError("Dados inválidos!", {"random_records": ["O campo é obrigatório."]})
        if n > len(df):
            raise ValidationError("Dados inválidos!", {"random_records": ["Amostra maior que o número de registros."]})
        return df.sample(n=n, replace=False)


class SystematicSamplingStrategy(ReductionStrategy):
    name = "amostragem_sistematica"

    def reduce(self, df, features, params):
        n = params.get("systematic_records")
        method = params.get("systematic_method")
        if not n:
            raise ValidationError("Dados inválidos!", {"systematic_records": ["O campo é obrigatório."]})
        if len(features) != 1:
            raise ValidationError("Dados inválidos!", {"features": ["Apenas uma feature deve ser selecionada."]})
        if method not in ("maiores", "menores"):
            raise ValidationError("Dados inválidos!", {"systematic_method": ["Escolha entre 'maiores' ou 'menores'."]})
        feature = features[0]
        return df.nlargest(n, feature) if method == "maiores" else df.nsmallest(n, feature)


_REGISTRY = {s.name: s for s in (PCAStrategy, RandomSamplingStrategy, SystematicSamplingStrategy)}


def get_strategy(name: str) -> ReductionStrategy:
    strategy = _REGISTRY.get(name)
    if strategy is None:
        raise ValidationError("Dados inválidos!", {"methods": [f"Método inválido: {name}."]})
    return strategy()
```

- [ ] **Step 4: Implementar `schemas/data_mining/reduction.py`**

```python
from pydantic import BaseModel, Field


class DataReductionSchema(BaseModel):
    features: list[str] = Field(min_length=1)
    methods: str
    target: str | None = None
    random_records: int | None = None
    systematic_records: int | None = None
    systematic_method: str | None = None
```

- [ ] **Step 5: Implementar `services/data_mining/reduction_service.py`**

```python
from app.common.decorators import transactional
from app.common.errors import NotFoundError, ValidationError
from app.common.files import dataframe_to_csv_upload, read_csv
from app.data_mining.reduction.strategies import get_strategy
from app.models import CleanDataset
from app.repositories.clean_dataset_repository import CleanDatasetRepository
from app.repositories.dataset_repository import DatasetRepository


class DataReductionService:
    def __init__(self, datasets: DatasetRepository, clean_datasets: CleanDatasetRepository, storage):
        self._datasets = datasets
        self._clean = clean_datasets
        self._storage = storage

    @transactional
    def reduce(self, dataset_id: int, data, user_id: int) -> CleanDataset:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")

        existing = self._clean.get_by_dataset(dataset.id)
        source_url = existing.file_url if existing else dataset.file_url

        df = read_csv(source_url)
        invalid = [f for f in data.features if f not in df.columns]
        if invalid:
            raise ValidationError("Dados inválidos!", {"features": [f"Campos não registrados: {', '.join(invalid)}"]})

        strategy = get_strategy(data.methods)
        reduced = strategy.reduce(df, data.features, data.model_dump())

        base_name = dataset.file_url.split("/")[-1].split(".")[0].split("_")[0]
        upload, size_label = dataframe_to_csv_upload(reduced, f"{base_name}_reduced.csv")
        file_url = self._storage.upload(upload)

        if existing:
            if existing.file_url:
                self._storage.delete(existing.file_url)
            self._clean.delete(existing)

        return self._clean.add(CleanDataset(
            size_file=size_label, file_url=file_url, dataset_id=dataset.id, user_id=user_id,
        ))
```

- [ ] **Step 6: Adicionar rota em `preprocessing_controller.py`**

```python
from app.schemas.data_mining.reduction import DataReductionSchema


@preprocessing_bp.post("/data-reduction/<int:dataset_id>")
@login_required
@handle_errors
def data_reduction(dataset_id):
    data = DataReductionSchema.model_validate(request.get_json(silent=True) or {})
    clean = current_app.services["reduction"].reduce(dataset_id, data, current_user.id)
    payload = {"reduced_dataset": {"id": clean.id, "size_file": clean.size_file, "file_url": clean.file_url}}
    body, status = success_payload("Redução de dados realizada com sucesso!", payload)
    return jsonify(body), status
```

- [ ] **Step 7: Registrar serviço no wiring (Task 14) e rodar**

Run: `pytest tests/integration/test_reduction.py -v`
Expected: PASS (2 passed)

- [ ] **Step 8: Commit**

```bash
git add api/app/data_mining/reduction api/app/schemas/data_mining/reduction.py api/app/services/data_mining/reduction_service.py api/app/controllers/data_mining/preprocessing_controller.py tests/integration/test_reduction.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: refatora data reduction com strategy pattern"
```

---

## Task 12: Data Mining — Classification (Strategy)

**Files:**
- Create: `api/app/data_mining/classification/__init__.py` (vazio), `api/app/data_mining/classification/strategies.py`
- Create: `api/app/schemas/data_mining/classification.py`
- Create: `api/app/services/data_mining/classification_service.py`
- Create: `api/app/controllers/data_mining/classification_controller.py`
- Test: `tests/integration/test_classification.py`

> Endpoint: `POST /api/classification/<int:dataset_id>` (login). JSON: `features` (lista, ≥1), `target` (coluna, ≠ das features), `classification_method` (knn), `distance_metric` (euclidean|manhattan|minkowski|mahalanobis, default euclidean), `k_neighbors` (int ≥1, default 5), `test_size` (0.1–0.9, default 0.3), `use_clean_dataset` (bool, default False). Usa o arquivo limpo se `use_clean_dataset` e existir; senão o original. Não cria CleanDataset — retorna métricas. Dataset precisa ≥4 amostras. Resposta: dict com `algorithm_info`, `dataset_info`, `performance_metrics`, `confusion_matrix`, `plot_algorithm` (ver formato no controller antigo `classification_controller.py`).

- [ ] **Step 1: Escrever testes que falham**

Create `tests/integration/test_classification.py`:

```python
import pandas as pd

from app.data_mining.classification.strategies import get_strategy, KNNStrategy


def test_knn_strategy_returns_metrics():
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8],
        "y": [1, 2, 3, 4, 5, 6, 7, 8],
        "label": [0, 0, 0, 0, 1, 1, 1, 1],
    })
    result = KNNStrategy().run(df, features=["x", "y"], target="label",
                               params={"k_neighbors": 3, "distance_metric": "euclidean", "test_size": 0.25})
    assert "performance_metrics" in result
    assert result["algorithm_info"]["k_neighbors"] == 3


def test_classification_endpoint(auth_client, s3, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    from app.services.data_mining import classification_service as mod
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5, 6, 7, 8],
        "y": [1, 2, 3, 4, 5, 6, 7, 8],
        "label": [0, 0, 0, 0, 1, 1, 1, 1],
    })
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    payload = {"features": ["x", "y"], "target": "label", "classification_method": "knn",
               "k_neighbors": 3, "test_size": 0.25}
    resp = client.post(f"/api/classification/{ds.id}", json=payload)
    assert resp.status_code == 200
    assert "performance_metrics" in resp.get_json()["data"]
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_classification.py -v`
Expected: FAIL

- [ ] **Step 3: Implementar `data_mining/classification/strategies.py`**

```python
from abc import ABC, abstractmethod

import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier

from app.common.errors import ValidationError


class ClassificationStrategy(ABC):
    name: str

    @abstractmethod
    def run(self, df: pd.DataFrame, features: list[str], target: str, params: dict) -> dict: ...


class KNNStrategy(ClassificationStrategy):
    name = "knn"

    def run(self, df, features, target, params):
        X, y = df[features], df[target]
        mask = ~(X.isnull().any(axis=1) | y.isnull())
        X, y = X[mask], y[mask]
        if len(X) == 0:
            raise ValidationError("Dados inválidos!", {"dataset": ["Todas as amostras possuem valores ausentes."]})

        k = params["k_neighbors"]
        metric = params["distance_metric"]
        test_size = params["test_size"]
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=42, stratify=y)
        model = KNeighborsClassifier(n_neighbors=k, metric=metric)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        return {
            "algorithm_info": {
                "name": "K-Nearest Neighbors", "type": "Classification",
                "k_neighbors": k, "distance_metric": metric,
                "features_used": features, "target": target,
            },
            "dataset_info": {
                "total_samples": len(X), "features_count": len(features),
                "train_samples": len(X_train), "test_samples": len(X_test),
                "test_size_percentage": round(test_size * 100, 2),
                "unique_classes": len(y.unique()),
                "class_distribution": y.value_counts().to_dict(),
            },
            "performance_metrics": classification_report(y_test, y_pred, output_dict=True, zero_division=0),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "plot_algorithm": {
                "x": X_test.iloc[:, 0].tolist(), "y": X_test.iloc[:, 1].tolist(),
                "predicted_labels": y_pred.tolist(), "true_labels": y_test.tolist(),
            },
        }


_REGISTRY = {s.name: s for s in (KNNStrategy,)}


def get_strategy(name: str) -> ClassificationStrategy:
    strategy = _REGISTRY.get(name)
    if strategy is None:
        raise ValidationError("Dados inválidos!", {"classification_method": [f"Método '{name}' não é válido."]})
    return strategy()
```

- [ ] **Step 4: Implementar `schemas/data_mining/classification.py`**

```python
from pydantic import BaseModel, Field, model_validator

_VALID_METRICS = {"euclidean", "manhattan", "minkowski", "mahalanobis"}


class ClassificationSchema(BaseModel):
    features: list[str] = Field(min_length=1)
    target: str
    classification_method: str = "knn"
    distance_metric: str = "euclidean"
    k_neighbors: int = Field(default=5, ge=1)
    test_size: float = Field(default=0.3, ge=0.1, le=0.9)
    use_clean_dataset: bool = False

    @model_validator(mode="after")
    def _check(self):
        if self.distance_metric not in _VALID_METRICS:
            raise ValueError(f"Métrica de distância '{self.distance_metric}' não é válida.")
        if self.target in self.features:
            raise ValueError("O campo target não pode estar incluído nas features.")
        return self
```

- [ ] **Step 5: Implementar `services/data_mining/classification_service.py`**

```python
from app.common.errors import NotFoundError, ValidationError
from app.common.files import read_csv
from app.data_mining.classification.strategies import get_strategy
from app.repositories.clean_dataset_repository import CleanDatasetRepository
from app.repositories.dataset_repository import DatasetRepository


class ClassificationService:
    def __init__(self, datasets: DatasetRepository, clean_datasets: CleanDatasetRepository):
        self._datasets = datasets
        self._clean = clean_datasets

    def classify(self, dataset_id: int, data, user_id: int) -> dict:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")

        file_url = dataset.file_url
        if data.use_clean_dataset:
            clean = self._clean.get_by_dataset(dataset.id)
            if not clean:
                raise NotFoundError("Dataset limpo não encontrado!")
            file_url = clean.file_url

        df = read_csv(file_url)
        if len(df) < 4:
            raise ValidationError("Dados inválidos!", {"dataset": ["O dataset deve ter pelo menos 4 amostras."]})
        invalid = [f for f in data.features if f not in df.columns]
        if invalid:
            raise ValidationError("Dados inválidos!", {"features": [f"Campos não registrados: {', '.join(invalid)}"]})
        if data.target not in df.columns:
            raise ValidationError("Dados inválidos!", {"target": [f"O campo target '{data.target}' não está registrado."]})

        strategy = get_strategy(data.classification_method)
        return strategy.run(df, data.features, data.target, data.model_dump())
```

> Não tem `@transactional`: classification não escreve no banco (read-only).

- [ ] **Step 6: Implementar `controllers/data_mining/classification_controller.py`**

```python
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.data_mining.classification import ClassificationSchema

classification_bp = Blueprint("classification", __name__)


@classification_bp.post("/<int:dataset_id>")
@login_required
@handle_errors
def classify(dataset_id):
    data = ClassificationSchema.model_validate(request.get_json(silent=True) or {})
    results = current_app.services["classification"].classify(dataset_id, data, current_user.id)
    body, status = success_payload(
        f"Algoritmo de classificação {data.classification_method.upper()} executado com sucesso!", results
    )
    return jsonify(body), status
```

- [ ] **Step 7: Registrar serviço/blueprint no wiring (Task 14) e rodar**

Run: `pytest tests/integration/test_classification.py -v`
Expected: PASS (2 passed)

- [ ] **Step 8: Commit**

```bash
git add api/app/data_mining/classification api/app/schemas/data_mining/classification.py api/app/services/data_mining/classification_service.py api/app/controllers/data_mining/classification_controller.py tests/integration/test_classification.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: refatora classification com strategy pattern"
```

---

## Task 13: Data Mining — Visualization

**Files:**
- Create: `api/app/data_mining/visualization/__init__.py` (vazio), `api/app/data_mining/visualization/measures.py`
- Create: `api/app/schemas/data_mining/visualization.py`
- Create: `api/app/services/data_mining/visualization_service.py`
- Create: `api/app/controllers/data_mining/visualization_controller.py`
- Test: `tests/integration/test_visualization.py`

> 4 endpoints (login), todos `POST /<grupo>/<int:dataset_id>`: `measure-central-tendency`, `dispersion-measure`, `shape-measure`, `association-measure`. JSON: `features` (lista), `visualization_method` (depende do grupo — ver mapas), `use_clean_dataset` (bool). Associação exige exatamente 2 features. Read-only (sem banco). As funções de medida (média, mediana, moda, desvio, etc.) são portadas 1:1 do `data_visualization_controller.py` atual para `measures.py`, organizadas em 4 registries por grupo.

> **Estratégia de portabilidade:** as funções `get_*_results`, `get_frequency_distribution`, `calculate_mean_by_class`, `interpret_*` etc. do controller antigo (`api/app/controllers/data_mining/data_visualization_controller.py`, linhas 238–578) são copiadas para `measures.py` SEM alteração de lógica (só removendo o `response.` e mantendo as assinaturas `(file_url, features)`). Em vez de `pd.read_csv(file_url)` direto, importe `from app.common.files import read_csv` e use `read_csv(file_url)` para permitir monkeypatch nos testes.

- [ ] **Step 1: Escrever testes que falham**

Create `tests/integration/test_visualization.py`:

```python
import pandas as pd

from app.data_mining.visualization.measures import (
    CENTRAL_TENDENCY, DISPERSION, get_median_results, get_variance_results,
)


def test_median_results(monkeypatch):
    import app.data_mining.visualization.measures as mod
    df = pd.DataFrame({"idade": [10, 20, 30]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    result = get_median_results("fake", ["idade"])
    assert result["idade"] == 20


def test_registries_have_methods():
    assert "median" in CENTRAL_TENDENCY
    assert "variance" in DISPERSION


def test_central_tendency_endpoint(auth_client, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    import app.data_mining.visualization.measures as mod
    df = pd.DataFrame({"idade": [10, 20, 30, 40]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.post(f"/api/data-visualization/measure-central-tendency/{ds.id}",
                       json={"features": ["idade"], "visualization_method": "median"})
    assert resp.status_code == 200
    assert resp.get_json()["data"]["idade"] == 25


def test_association_requires_two_features(auth_client, monkeypatch):
    client, user = auth_client
    from tests.factories import make_project, make_dataset
    import app.data_mining.visualization.measures as mod
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    monkeypatch.setattr(mod, "read_csv", lambda url: df.copy())
    project = make_project(user)
    ds = make_dataset(user, project)
    resp = client.post(f"/api/data-visualization/association-measure/{ds.id}",
                       json={"features": ["a"], "visualization_method": "correlation"})
    assert resp.status_code == 422
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `pytest tests/integration/test_visualization.py -v`
Expected: FAIL

- [ ] **Step 3: Implementar `data_mining/visualization/measures.py`**

Portar as funções do controller antigo (linhas 238–578 de `data_visualization_controller.py`) substituindo `pd.read_csv(file_url)` por `read_csv(file_url)`. No topo:

```python
import numpy as np
import pandas as pd
from scipy import stats

from app.common.files import read_csv
```

Cole todas as funções: `get_frequency_distribution_results`, `get_mode_results`, `get_midpoint_results`, `get_median_results`, `get_weighted_average_results`, `get_mean_frequency_distribution_results`, `get_geometric_mean_results`, `get_harmonic_mean_results`, `get_skewness_results`, `get_kurtosis_results`, `get_frequency_distribution`, `calculate_mean_by_class`, `calculate_overall_mean_from_classes`, `get_amplitude_results`, `get_standard_deviation_results`, `get_variance_results`, `get_variation_coefficient_results`, `get_covariance_results`, `get_correlation_results`, `interpret_covariance`, `interpret_correlation`. (Lógica idêntica ao atual — não reescrever.) Ao final, adicione os 4 registries:

```python
CENTRAL_TENDENCY = {
    "frequency_distribution": get_frequency_distribution_results,
    "mode": get_mode_results,
    "midpoint": get_midpoint_results,
    "median": get_median_results,
    "weighted_average": get_weighted_average_results,
    "mean_frequency_distribution": get_mean_frequency_distribution_results,
    "geometric_mean": get_geometric_mean_results,
    "harmonic_mean": get_harmonic_mean_results,
}
DISPERSION = {
    "amplitude": get_amplitude_results,
    "standard_deviation": get_standard_deviation_results,
    "variance": get_variance_results,
    "variation_coefficient": get_variation_coefficient_results,
}
SHAPE = {"skewness": get_skewness_results, "kurtosis": get_kurtosis_results}
ASSOCIATION = {"covariance": get_covariance_results, "correlation": get_correlation_results}
```

- [ ] **Step 4: Implementar `schemas/data_mining/visualization.py`**

```python
from pydantic import BaseModel, Field


class VisualizationSchema(BaseModel):
    features: list[str] = Field(min_length=1)
    visualization_method: str
    use_clean_dataset: bool = False
```

- [ ] **Step 5: Implementar `services/data_mining/visualization_service.py`**

```python
from app.common.errors import NotFoundError, ValidationError
from app.data_mining.visualization.measures import ASSOCIATION, CENTRAL_TENDENCY, DISPERSION, SHAPE
from app.repositories.clean_dataset_repository import CleanDatasetRepository
from app.repositories.dataset_repository import DatasetRepository

_GROUPS = {
    "central_tendency": CENTRAL_TENDENCY,
    "dispersion": DISPERSION,
    "shape": SHAPE,
    "association": ASSOCIATION,
}


class VisualizationService:
    def __init__(self, datasets: DatasetRepository, clean_datasets: CleanDatasetRepository):
        self._datasets = datasets
        self._clean = clean_datasets

    def measure(self, group: str, dataset_id: int, data, user_id: int) -> dict:
        dataset = self._datasets.get_owned(dataset_id, user_id)
        if not dataset:
            raise NotFoundError("Base de dados não encontrada!")

        registry = _GROUPS[group]
        method = registry.get(data.visualization_method)
        if method is None:
            raise ValidationError("Dados inválidos!", {"visualization_method": [f"Método '{data.visualization_method}' não é válido para {group}."]})

        if group == "association" and len(data.features) != 2:
            raise ValidationError("Dados inválidos!", {"features": ["Para medidas de associação é necessário exatamente 2 features."]})

        file_url = dataset.file_url
        if data.use_clean_dataset:
            clean = self._clean.get_by_dataset(dataset.id)
            if not clean:
                raise NotFoundError("Dataset limpo não encontrado!")
            file_url = clean.file_url

        return method(file_url, data.features)
```

- [ ] **Step 6: Implementar `controllers/data_mining/visualization_controller.py`**

```python
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required

from app.common.decorators import handle_errors
from app.common.responses import success_payload
from app.schemas.data_mining.visualization import VisualizationSchema

visualization_bp = Blueprint("data-visualization", __name__)

_ROUTES = {
    "measure-central-tendency": ("central_tendency", "tendência central"),
    "dispersion-measure": ("dispersion", "dispersão"),
    "shape-measure": ("shape", "forma"),
    "association-measure": ("association", "associação"),
}


def _make_handler(path, group, label):
    @handle_errors
    def handler(dataset_id):
        data = VisualizationSchema.model_validate(request.get_json(silent=True) or {})
        results = current_app.services["visualization"].measure(group, dataset_id, data, current_user.id)
        body, status = success_payload(f"Visualização de medidas de {label} realizada com sucesso!", results)
        return jsonify(body), status

    handler.__name__ = f"viz_{group}"
    return handler


for _path, (_group, _label) in _ROUTES.items():
    visualization_bp.add_url_rule(
        f"/{_path}/<int:dataset_id>", view_func=login_required(_make_handler(_path, _group, _label)), methods=["POST"]
    )
```

- [ ] **Step 7: Registrar serviço/blueprint no wiring (Task 14) e rodar**

Run: `pytest tests/integration/test_visualization.py -v`
Expected: PASS (4 passed)

- [ ] **Step 8: Commit**

```bash
git add api/app/data_mining/visualization api/app/schemas/data_mining/visualization.py api/app/services/data_mining/visualization_service.py api/app/controllers/data_mining/visualization_controller.py tests/integration/test_visualization.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: refatora data visualization com registries por grupo de medida"
```

---

## Task 14: App factory, wiring de dependências e remoção do código antigo

> **Esta task é pré-requisito de execução das Tasks 5–13** (os controllers usam `current_app.services[...]` e os blueprints precisam estar registrados). Recomenda-se aplicar os Steps 1–6 logo após a Task 4 (fundação), e adicionar cada serviço/blueprint ao wiring conforme cada domínio for implementado. Os Steps 7–9 (remoção de código morto) só ao final, quando tudo passar.

**Files:**
- Modify: `api/app/__init__.py` (reescrever `create_app` + `wire_services`)
- Create: `api/app/controllers/__init__.py` (`register_controllers`)
- Modify: `api/app/models/clean_dataset.py` (remover event listener S3)
- Delete (Step 7+): `api/app/routes/`, `api/app/forms/`, `api/app/controllers/s3_controller.py`, `api/app/controllers/user_controller.py` (antigo), `project_controller.py` (antigo), `dataset_controller.py` (antigo), `auth_controller.py` (antigo), `api/app/controllers/data_mining/preprocessing/`, `api/app/controllers/data_mining/classification_controller.py` (antigo), `data_visualization_controller.py` (antigo), `api/app/response_handlers.py`, `api/app/swagger/`
- Test: roda toda a suíte

- [ ] **Step 1: Implementar `controllers/__init__.py`**

```python
def register_controllers(app):
    from app.controllers.auth_controller import auth_bp
    from app.controllers.user_controller import user_bp
    from app.controllers.project_controller import project_bp
    from app.controllers.dataset_controller import dataset_bp
    from app.controllers.data_mining.preprocessing_controller import preprocessing_bp
    from app.controllers.data_mining.visualization_controller import visualization_bp
    from app.controllers.data_mining.classification_controller import classification_bp

    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(project_bp, url_prefix="/api/projects")
    app.register_blueprint(dataset_bp, url_prefix="/api/datasets")
    app.register_blueprint(preprocessing_bp, url_prefix="/api/preprocessing")
    app.register_blueprint(visualization_bp, url_prefix="/api/data-visualization")
    app.register_blueprint(classification_bp, url_prefix="/api/classification")
```

> Durante a execução incremental (Tasks 5–13), registre apenas os blueprints já implementados — comente os imports/registros pendentes e descomente conforme avança.

- [ ] **Step 2: Reescrever `api/app/__init__.py`**

```python
from dotenv import load_dotenv
from flask import Flask, jsonify

from app.config import Config
from app.controllers import register_controllers
from app.extensions import cors, db, login_manager, migrate

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
    from app.services.user_service import UserService
    from app.services.project_service import ProjectService
    from app.services.dataset_service import DatasetService
    from app.services.data_mining.cleaning_service import DataCleaningService
    from app.services.data_mining.normalization_service import DataNormalizationService
    from app.services.data_mining.reduction_service import DataReductionService
    from app.services.data_mining.classification_service import ClassificationService
    from app.services.data_mining.visualization_service import VisualizationService
    from app.storage.s3_client import StorageClient

    session = db.session
    storage = StorageClient(app.config["S3_BUCKET"], app.config["S3_KEY"], app.config["S3_SECRET"])

    users = UserRepository(session)
    projects = ProjectRepository(session)
    datasets = DatasetRepository(session)
    cleans = CleanDatasetRepository(session)

    app.services = {
        "auth": AuthService(users),
        "user": UserService(users, storage),
        "project": ProjectService(projects, storage),
        "dataset": DatasetService(datasets, projects, storage),
        "cleaning": DataCleaningService(datasets, cleans, storage),
        "normalization": DataNormalizationService(datasets, cleans, storage),
        "reduction": DataReductionService(datasets, cleans, storage),
        "classification": ClassificationService(datasets, cleans),
        "visualization": VisualizationService(datasets, cleans),
    }


def register_home_route(app):
    @app.route("/", methods=["GET"])
    def home():
        return jsonify({
            "Mensagem": "Bem-vindo a API do EasyMiner",
            "OBS": "Para ter acesso a documentação acesse a URL /apidocs",
        }), 200


@login_manager.user_loader
def load_user(user_id):
    from app.models import User
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"success": False, "message": "Não autorizado!", "errors": None}), 401
```

> `db.session` é um scoped session proxy do Flask-SQLAlchemy: usar como argumento dos repos funciona porque a referência resolve a sessão ativa do contexto a cada uso. `unauthorized_handler` garante 401 JSON (não redirect) — necessário para os testes `*_requires_login`.

- [ ] **Step 3: Remover event listener de `models/clean_dataset.py`** — substituir o arquivo por:

```python
from datetime import datetime

from app.extensions import db


class CleanDataset(db.Model):
    __tablename__ = "clean_datasets"
    id = db.Column(db.Integer, primary_key=True)
    size_file = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    dataset_id = db.Column(db.Integer, db.ForeignKey("datasets.id"), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=None, onupdate=datetime.utcnow)

    dataset = db.relationship("Dataset", back_populates="clean_dataset")
    user = db.relationship("User", back_populates="clean_datasets")
```

- [ ] **Step 4: Ajustar `models/user.py`** — trocar `from app import db` por `from app.extensions import db` (consistência; evita import circular com a nova factory).

- [ ] **Step 5: Rodar a suíte inteira**

Run: `pytest -v`
Expected: todos os testes das Tasks 1–13 PASSAM. Se algum domínio ainda não foi implementado no momento em que você roda, registre só o que existe.

- [ ] **Step 6: Commit do wiring**

```bash
git add api/app/__init__.py api/app/controllers/__init__.py api/app/models/clean_dataset.py api/app/models/user.py
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "refactor: religa app factory com wiring de services e remove IO escondido no ORM"
```

- [ ] **Step 7: Remover código antigo** (só após suíte 100% verde)

```bash
git rm -r api/app/routes api/app/forms api/app/response_handlers.py \
  api/app/controllers/s3_controller.py \
  api/app/controllers/data_mining/preprocessing \
  api/app/controllers/data_mining/data_visualization_controller.py
```

Os controllers procedurais antigos `auth_controller.py`, `user_controller.py`, `project_controller.py`, `dataset_controller.py` e `data_mining/classification_controller.py` foram SOBRESCRITOS pelos novos nas Tasks 5–12 (mesmos caminhos). Confirme que o conteúdo é o novo (com Blueprint) antes de prosseguir. O `data_visualization_controller.py` mudou de nome para `visualization_controller.py`, então o antigo é removido pelo `git rm` acima.

- [ ] **Step 8: Rodar a suíte de novo após limpeza**

Run: `pytest -v`
Expected: tudo verde, sem ImportError de módulos removidos. Se algo importava do antigo, corrija.

- [ ] **Step 9: Commit da limpeza**

```bash
git add -A
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "refactor: remove camadas antigas (routes, forms, controllers procedurais, response_handlers)"
```

---

## Task 15: Dependências e Swagger gerado do código

**Files:**
- Modify: `requirements.txt`
- Create: `api/app/docs/__init__.py` (vazio), `api/app/docs/openapi.py`
- Modify: `api/app/__init__.py` (registrar swagger)
- Modify: `api/app/extensions.py` (instanciar Swagger sem template estático)
- Delete: `api/app/swagger/` (já removido na Task 14 se aplicável)

> O projeto já usa `flasgger`. Em vez de migrar de biblioteca, mantemos flasgger mas geramos a spec a partir de docstrings YAML inline mínimas por endpoint + um template base montado dos schemas Pydantic via `model_json_schema()`. Isso mantém a doc próxima do código e elimina o `swagger.yaml` gigante desatualizado.

- [ ] **Step 1: Atualizar `requirements.txt`** — remover `Flask-WTF==1.2.1`, `WTForms==3.1.2`; adicionar:

```
pydantic[email]==2.9.2
pytest==8.3.3
pytest-flask==1.3.0
moto[s3]==5.0.18
```

Manter `flasgger`, `email_validator` (usado por pydantic[email]). Rodar `pip install -r requirements.txt` e confirmar que instala.

- [ ] **Step 2: Implementar `api/app/docs/openapi.py`** — monta o template base com os schemas Pydantic como components:

```python
from app.schemas.auth import LoginSchema
from app.schemas.user import UserCreateSchema, UserReadSchema, UserUpdateSchema
from app.schemas.project import ProjectCreateSchema, ProjectReadSchema, ProjectUpdateSchema, ProjectDetailSchema
from app.schemas.dataset import DatasetCreateSchema, DatasetReadSchema, DatasetUpdateSchema
from app.schemas.data_mining.cleaning import DataCleaningSchema
from app.schemas.data_mining.normalization import DataNormalizationSchema
from app.schemas.data_mining.reduction import DataReductionSchema
from app.schemas.data_mining.classification import ClassificationSchema
from app.schemas.data_mining.visualization import VisualizationSchema

_SCHEMAS = [
    LoginSchema, UserCreateSchema, UserReadSchema, UserUpdateSchema,
    ProjectCreateSchema, ProjectReadSchema, ProjectUpdateSchema, ProjectDetailSchema,
    DatasetCreateSchema, DatasetReadSchema, DatasetUpdateSchema,
    DataCleaningSchema, DataNormalizationSchema, DataReductionSchema,
    ClassificationSchema, VisualizationSchema,
]


def build_swagger_template() -> dict:
    definitions = {schema.__name__: schema.model_json_schema() for schema in _SCHEMAS}
    return {
        "openapi": "3.0.0",
        "info": {"title": "EasyMinerAPI", "version": "2.0.0",
                 "description": "API de KDD do EasyMiner — projetos, bases de dados e algoritmos de mineração."},
        "components": {"schemas": definitions},
    }


SWAGGER_CONFIG = {
    "headers": [],
    "specs": [{"endpoint": "apispec", "route": "/apispec.json"}],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/",
}
```

- [ ] **Step 3: Registrar Swagger no `create_app`** — adicionar em `api/app/__init__.py`:

```python
def register_swagger(app):
    from flasgger import Swagger
    from app.docs.openapi import SWAGGER_CONFIG, build_swagger_template
    Swagger(app, config=SWAGGER_CONFIG, template=build_swagger_template())
```

E chamar `register_swagger(app)` dentro de `create_app` (depois de `register_controllers`). Não registrar em `TestConfig` é opcional; pode deixar registrado (flasgger não atrapalha os testes).

- [ ] **Step 4: Adicionar docstrings YAML nos endpoints** — em cada view, adicionar docstring no formato flasgger. Exemplo em `auth_controller.py` `login`:

```python
def login():
    """Realiza login do usuário.
    ---
    tags: [Auth]
    requestBody:
      content:
        application/json:
          schema: {$ref: '#/components/schemas/LoginSchema'}
    responses:
      200: {description: Login realizado com sucesso}
      401: {description: Credenciais inválidas}
      422: {description: Dados inválidos}
    """
```

Repita o padrão (tags por domínio: Auth, Users, Projects, Datasets, Preprocessing, Visualization, Classification) com `$ref` aos schemas, para TODOS os endpoints. Mantenha curto — só tags, request schema e responses.

- [ ] **Step 5: Verificar a spec sobe**

Run: `pytest -v` (garante que nada quebrou)
Manual: subir o app local (`SQLALCHEMY_DATABASE_URI=sqlite:///dev.db flask --app wsgi run`) e abrir `http://localhost:5000/apidocs/` para confirmar que a UI renderiza com os schemas. Se não puder abrir browser, rodar:
`SQLALCHEMY_DATABASE_URI=sqlite:///dev.db python -c "from app import create_app; c=create_app().test_client(); print(c.get('/apispec.json').status_code)"`
Expected: `200`

- [ ] **Step 6: Commit**

```bash
git add requirements.txt api/app/docs api/app/__init__.py api/app/extensions.py api/app/controllers
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "feat: gera Swagger a partir dos schemas Pydantic e atualiza dependências"
```

---

## Task 16: Atualizar README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Reescrever README** cobrindo as seções abaixo. Mantenha a visão geral e a seção de instalação existentes (ajustando variáveis de ambiente), e ADICIONE/SUBSTITUA:

  1. **Tecnologias** — adicionar Pydantic, pytest. Remover menção a WTForms.
  2. **Arquitetura** — diagrama ASCII do pipeline (controller → schema → service → repository → storage/strategy) e descrição da responsabilidade de cada camada.
  3. **Estrutura de pastas** — árvore comentada de `api/app/`.
  4. **Fluxo de uma request** — exemplo passo a passo (ex.: `POST /api/datasets/create-dataset`).
  5. **Como adicionar** — (a) uma nova rota/domínio CRUD (schema → repo → service → controller → registrar no wiring/controllers), (b) uma nova Strategy de data mining (criar classe + registrar no `_REGISTRY`).
  6. **Convenções** — envelope de resposta `{success, message, data|errors}`, decorators `@handle_errors`/`@transactional`, validação via Pydantic.
  7. **Como rodar testes** — `pytest -v`; explicar fixtures (`client`, `auth_client`, `s3` via moto, SQLite em memória).
  8. **Variáveis de ambiente** — `SECRET_KEY`, `SQLALCHEMY_DATABASE_URI`, `S3_BUCKET`, `S3_KEY`, `S3_SECRET`.
  9. **Quebras de contrato da v2** — nota sobre envelope padronizado, formato de erro Pydantic e remoção do `/csrf-token`.

  Use o spec `docs/superpowers/specs/2026-05-27-easyminer-refactor-design.md` como fonte. Texto em PT-BR, claro e conciso.

- [ ] **Step 2: Revisar que não há instruções obsoletas** (ex.: `FLASK_APP=run.py` — o correto é `wsgi.py`; menção a CSRF token).

- [ ] **Step 3: Commit**

```bash
git add README.md
git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" commit -m "docs: reescreve README com a nova arquitetura, convenções e guia de extensão"
```

---

## Task 17: Verificação final e push

- [ ] **Step 1: Rodar suíte completa**

Run: `pytest -v`
Expected: 100% verde (todos os ~45 testes passam).

- [ ] **Step 2: Verificar que o app sobe sem erros**

Run: `SQLALCHEMY_DATABASE_URI=sqlite:///dev.db python -c "from app import create_app; create_app(); print('app ok')"`
Expected: `app ok` (com `PYTHONPATH=api` se necessário: `PYTHONPATH=api python -c ...`)

- [ ] **Step 3: Conferir que não sobrou import do código antigo**

Run: `grep -rn "response_handlers\|flask_wtf\|FlaskForm\|S3Controller\|from app.forms" api/ || echo "limpo"`
Expected: `limpo`

- [ ] **Step 4: Conferir git status e log**

Run: `git status && git log --oneline -15`
Expected: working tree limpo; commits das Tasks 1–16 presentes.

- [ ] **Step 5: Push**

```bash
git push origin develop
```

Expected: push aceito. Se o remoto rejeitar por divergência, NÃO force — investigar com `git fetch && git status` e reportar ao usuário.

---

## Self-Review (preenchido pelo autor do plano)

**Cobertura do spec:**
- §4 camadas → Tasks 1, 3, 4, 5–13 ✔
- §5 Pydantic → todos os schemas das Tasks 5–13 ✔
- §5 repository → Task 4 ✔
- §5 strategy data mining → Tasks 9–13 ✔
- §5 decorators/erros/envelope → Task 1 ✔
- §6 wiring → Task 14 ✔
- §7 testes integração por endpoint → cada domínio tem test_*.py ✔
- §8.1 swagger do código → Task 15 ✔
- §8.2 README → Task 16 ✔
- §9 quebras de contrato → refletidas (envelope, erros Pydantic, /csrf-token removido) ✔
- §10 deps adicionadas/removidas → Task 15 Step 1 ✔
- §12 workflow git (develop, commits semânticos, push) → commits por task + Task 17 ✔

**Dependência de ordem destacada:** Task 14 (wiring) precisa estar parcialmente aplicada para as Tasks 5–13 rodarem — isto está sinalizado no topo da Task 14 e nos Steps "registrar no wiring e rodar" de cada domínio.

**Consistência de nomes verificada:** `current_app.services["auth"|"user"|"project"|"dataset"|"cleaning"|"normalization"|"reduction"|"classification"|"visualization"]`, `get_strategy`, `read_csv`/`dataframe_to_csv_upload`/`bytes_to_mb_label`, `success_payload`/`error_payload`, `handle_errors`/`transactional` — usados de forma idêntica em todas as tasks.
