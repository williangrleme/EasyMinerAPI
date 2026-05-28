# EasyMinerAPI — Refatoração para Arquitetura OO Limpa

**Data:** 2026-05-27
**Branch:** `develop`
**Tipo:** Refator big bang (reescrita arquitetural completa, sem mudanças de funcionalidade)

## 1. Motivação

A base de código atual sofre dos seguintes problemas:

- **"Controllers" são módulos procedurais** (funções soltas em `api/app/controllers/**`) que misturam: parsing HTTP, validação, regra de negócio, persistência, integração com S3 e formatação de resposta. Viola SRP.
- **DRY violado**: padrão `try/except/db.session.rollback()/log_error/handle_internal_server_error_response` repetido em praticamente todas as funções de escrita; `format_*_data` duplicado entre arquivos; `S3Controller()` instanciado em cada chamada.
- **Acoplamento ao framework**: regra de negócio chama `Model.query`, `db.session`, `current_user` direto — não há como testar isoladamente sem subir o Flask inteiro.
- **Validação inadequada**: WTForms (Flask-WTF) é desenhado para forms HTML, não APIs JSON; produz mensagens de erro estruturadas de forma inconsistente.
- **Sem testes** — qualquer mudança é cega.
- **Swagger desincronizado**: `swagger.yaml` mantido à mão, sai do ar a cada mudança real.

## 2. Objetivos

- Aplicar SOLID (especialmente SRP, DIP, OCP), DRY, clean code.
- Estabelecer camadas claras com responsabilidades únicas e dependências invertidas via interfaces.
- Eliminar boilerplate por meio de decorators/middlewares centralizados.
- Tornar o domínio testável independente do framework.
- Manter o comportamento funcional dos endpoints; pequenas quebras de contrato (formato de erro, envelope de resposta) são permitidas.
- Cobrir 100% dos endpoints com testes de integração.
- Documentação (README + Swagger) sempre em sincronia com o código.

## 3. Decisões de Design

| Tema | Decisão |
|---|---|
| Estratégia | Big bang (reescrita completa na branch `develop`) |
| Compatibilidade de API | Pode quebrar coisas pequenas (envelope/erros padronizados) |
| Validação | Pydantic v2 (substitui WTForms/Flask-WTF) |
| Acesso a dados | Repository pattern sobre SQLAlchemy |
| Algoritmos de data mining | Strategy pattern com registry |
| Testes | Integração por endpoint (pytest + Flask test client + SQLite em memória + moto para S3) |
| Organização de pacotes | Por camada técnica (controllers/services/repositories/schemas/models) |
| Documentação API | OpenAPI gerado dos schemas Pydantic (substitui `swagger.yaml` estático) |
| Workflow git | Trabalho direto em `develop`, commits semânticos por fase, push ao final |

## 4. Arquitetura

### 4.1 Pipeline de uma request

```
HTTP request
  → Blueprint/Route (controllers/*)              # parse HTTP, status, delega
    → Pydantic Schema                            # valida entrada
    → Service                                    # regra de negócio, orquestração
      → Repository                               # único ponto que toca SQLAlchemy
      → StorageClient / Strategy                 # S3, algoritmos
    → Schema serializa resposta
  → Controller devolve (json, status)
```

### 4.2 Estrutura de pastas

```
api/app/
  __init__.py              # create_app(), wiring de dependências
  config.py
  extensions.py            # db, migrate, login_manager, cors

  controllers/             # blueprints Flask, finos
    auth_controller.py
    user_controller.py
    project_controller.py
    dataset_controller.py
    data_mining/
      cleaning_controller.py
      normalization_controller.py
      reduction_controller.py
      classification_controller.py
      visualization_controller.py

  schemas/                 # Pydantic v2
    auth.py
    user.py
    project.py
    dataset.py
    data_mining/...

  services/                # regra de negócio
    auth_service.py
    user_service.py
    project_service.py
    dataset_service.py
    data_mining/
      cleaning_service.py
      normalization_service.py
      reduction_service.py
      classification_service.py
      visualization_service.py

  repositories/            # acesso a dados
    base.py                # AbstractRepository
    user_repository.py
    project_repository.py
    dataset_repository.py
    clean_dataset_repository.py

  models/                  # SQLAlchemy ORM (mantidos, limpos)
    user.py
    project.py
    dataset.py
    clean_dataset.py

  storage/
    s3_client.py           # encapsula boto3, init no create_app

  data_mining/
    cleaning/strategies/   # MeanFill, MedianFill, ModeFill
    normalization/strategies/  # MinMax, ZScore
    reduction/strategies/  # PCA, sampling
    classification/strategies/ # algoritmos com fit/predict
    visualization/         # geradores de gráfico

  common/
    errors.py              # DomainError e subclasses
    decorators.py          # @handle_errors, @transactional
    responses.py           # envelope padrão

tests/
  conftest.py              # fixtures: app, client, db, s3_mock, auth helper
  integration/
    test_auth.py
    test_users.py
    test_projects.py
    test_datasets.py
    test_data_mining_cleaning.py
    test_data_mining_normalization.py
    test_data_mining_reduction.py
    test_data_mining_classification.py
    test_data_mining_visualization.py
```

## 5. Padrões de Código

### 5.1 Controller (fino)

```python
@datasets_bp.post("")
@login_required
@handle_errors
def create_dataset():
    payload = DatasetCreateSchema.from_request(request)
    dataset = dataset_service.create(payload, current_user.id)
    return DatasetReadSchema.model_validate(dataset).model_dump(), 201
```

### 5.2 Service (regra, injeção por construtor)

```python
class DatasetService:
    def __init__(self, repo: AbstractDatasetRepository, storage: StorageClient):
        self._repo = repo
        self._storage = storage

    @transactional
    def create(self, data: DatasetCreateSchema, user_id: int) -> Dataset:
        file_url, size = self._storage.upload_csv(data.csv_file, user_id, data.name)
        return self._repo.add(Dataset(
            name=data.name,
            description=data.description,
            size_file=size,
            file_url=file_url,
            project_id=data.project_id,
            user_id=user_id,
        ))
```

### 5.3 Repository

```python
class AbstractDatasetRepository(ABC):
    @abstractmethod
    def get(self, id: int) -> Dataset | None: ...
    @abstractmethod
    def list_by_user(self, user_id: int) -> list[Dataset]: ...
    @abstractmethod
    def add(self, dataset: Dataset) -> Dataset: ...
    @abstractmethod
    def delete(self, dataset: Dataset) -> None: ...

class DatasetRepository(AbstractDatasetRepository):
    def __init__(self, session): self._session = session
    def get(self, id): return self._session.get(Dataset, id)
    ...
```

### 5.4 Erros de domínio

```python
class DomainError(Exception): status = 400
class NotFoundError(DomainError): status = 404
class UnauthorizedError(DomainError): status = 401
class ValidationError(DomainError): status = 422
class ExternalServiceError(DomainError): status = 502
```

### 5.5 Decorators centralizam boilerplate

```python
def handle_errors(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        try:
            return fn(*a, **kw)
        except DomainError as e:
            return error_response(e.status, str(e))
        except PydanticValidationError as e:
            return error_response(422, e.errors())
        except Exception:
            logger.exception("unhandled")
            db.session.rollback()
            return error_response(500, "Erro interno do servidor")
    return wrapper

def transactional(fn):
    @wraps(fn)
    def wrapper(self, *a, **kw):
        try:
            result = fn(self, *a, **kw)
            db.session.commit()
            return result
        except Exception:
            db.session.rollback()
            raise
    return wrapper
```

### 5.6 Envelope de resposta

Sucesso:
```json
{ "success": true, "message": "...", "data": {...} }
```

Erro:
```json
{ "success": false, "message": "...", "errors": {...} }
```

### 5.7 Strategy para data mining

```python
class MissingValueStrategy(ABC):
    name: str
    @abstractmethod
    def apply(self, series: pd.Series) -> pd.Series: ...

class MeanFillStrategy(MissingValueStrategy):
    name = "media"
    def apply(self, s): return s.fillna(s.mean().round(4))

STRATEGIES: dict[str, type[MissingValueStrategy]] = {
    "media": MeanFillStrategy,
    "mediana": MedianFillStrategy,
    "moda": ModeFillStrategy,
}
```

Adicionar técnica nova = novo arquivo + uma entrada no registry. Zero edição em código existente (OCP).

## 6. Dependency Wiring

Sem container DI; instanciação no `create_app()` e injeção via construtor. Services como singletons no `app.extensions` ou expostos via `flask.g`. Mantém simples (YAGNI).

```python
def create_app():
    app = Flask(__name__)
    register_extensions(app)
    register_controllers(app)
    register_error_handlers(app)
    wire_services(app)
    return app

def wire_services(app):
    app.s3_client = S3Client(app.config)
    app.services = {
        "dataset": DatasetService(DatasetRepository(db.session), app.s3_client),
        ...
    }
```

## 7. Testes

Stack: `pytest`, `pytest-flask`, `moto[s3]`, `factory-boy`.

Para cada endpoint, no mínimo:
- happy path (200/201)
- 401 (não autenticado)
- 404 (recurso inexistente / pertencente a outro usuário)
- 422 (payload inválido)

Banco SQLite em memória recriado por teste (fixture). S3 via `moto`. Login via fixture helper. Tudo roda em segundos.

## 8. Documentação

### 8.1 Swagger / OpenAPI

- Remover `api/app/swagger/swagger.yaml`.
- Integrar `flask-pydantic-spec` (ou `apispec` + plugin Pydantic).
- Cada controller anota request/response schemas; OpenAPI 3 gerado em runtime.
- Swagger UI exposto em `/apidocs` (mantém URL atual).

### 8.2 README

Reescrever cobrindo:
- Visão geral do projeto (preservada).
- **Arquitetura nova** com diagrama ASCII das camadas.
- Estrutura de pastas e responsabilidades.
- Como adicionar: nova rota, novo domínio, nova Strategy de data mining.
- Como rodar testes (`pytest`, comandos).
- Variáveis de ambiente consolidadas.
- Convenções: Pydantic schemas, decorators de erro/transação.

## 9. Quebras de Contrato Permitidas

- Envelope de resposta padronizado em todos os endpoints (alguns hoje retornam formatos diferentes).
- Formato de erro de validação muda de dict WTForms para lista Pydantic.
- Mensagens de erro padronizadas em PT-BR.
- URLs, métodos HTTP e códigos de status permanecem os mesmos.

## 10. Dependências

**Adicionadas**: `pydantic>=2`, `pytest`, `pytest-flask`, `moto[s3]`, `factory-boy`, `flask-pydantic-spec` (ou equivalente).

**Removidas**: `Flask-WTF`, `WTForms`, `Flask-CSRFProtect` (CSRF não se aplica a API JSON com auth via session — vale revisitar autenticação em refactor futuro, fora deste escopo).

## 11. Plano de Execução (fases internas)

Mesmo sendo big bang, executar em ordem para reduzir caos:

1. **Setup**: dependências, `common/` (errors, decorators, responses), estrutura de pastas.
2. **Fundação**: `AbstractRepository`, `StorageClient`, fixtures de teste, conftest.
3. **Auth**: schemas, service, repository, controller, testes.
4. **Users**: idem.
5. **Projects**: idem.
6. **Datasets** (+ CleanDataset): idem.
7. **Data mining — cleaning**: strategies + service + controller + testes.
8. **Data mining — normalization**: idem.
9. **Data mining — reduction**: idem.
10. **Data mining — classification**: idem.
11. **Data mining — visualization**: idem.
12. **Swagger automatizado**: integrar, remover yaml antigo.
13. **README reescrito.**
14. **Remoção de código morto** (forms/, controllers antigos, response_handlers antigo).
15. **Rodar suíte completa, garantir verde, push.**

## 12. Workflow Git

- Trabalhar diretamente em `develop` (já é a branch ativa).
- Commits semânticos seguindo convenção atual do repo: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`.
- Um commit por fase do plano de execução (commits revisáveis, não um commit gigante).
- Ao final: `git push origin develop`.

## 13. Riscos e Mitigações

| Risco | Mitigação |
|---|---|
| Big bang quebra comportamento existente | Suíte de integração por endpoint cobrindo happy + erros antes de cada migração de domínio |
| Tempo de execução longo | Plano em 15 fases independentes commitáveis; possível pausar e retomar |
| Mudança de validação rompe clientes | Documentar quebras na seção 9 do README; quebras avisadas no commit message |
| Swagger automático não cobre tudo | Plugins atuais (flask-pydantic-spec) cobrem 100% do necessário; testes garantem que schemas batem com payloads reais |

## 14. Fora de Escopo

- Migração de auth de session-cookie para JWT/token (fica para refactor futuro).
- Mudança de banco de dados ou cloud provider.
- Novas funcionalidades de data mining.
- Frontend.
- CI/CD (mantém Procfile/Dockerfile/fly.toml atuais).
