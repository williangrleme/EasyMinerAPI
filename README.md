# EasyMinerAPI

Repositório para o back-end da aplicação EasyMiner.

## Descrição

EasyMiner é uma aplicação desenvolvida para facilitar a execução de algoritmos de KDD (Knowledge Discovery in Databases) em conjuntos de dados. A API oferece gerenciamento de usuários, projetos e bases de dados, e aplica sobre essas bases algoritmos de pré-processamento (limpeza, normalização, redução), classificação e visualização estatística.

---

## Tecnologias

| Tecnologia | Uso |
|---|---|
| Flask 3 | Framework web / roteamento |
| Flask-SQLAlchemy / Flask-Migrate | ORM e migrações de banco de dados |
| Flask-Login | Autenticação via sessão |
| Flask-Cors | Controle de CORS |
| Pydantic v2 | Validação de entrada e serialização de resposta |
| flasgger | Geração do Swagger UI a partir das docstrings |
| pandas | Manipulação de dados CSV |
| scikit-learn | Algoritmos de data mining (PCA, KNN, scalers) |
| boto3 | Upload/download de arquivos no Amazon S3 |
| pytest / pytest-flask / moto | Testes de integração com S3 mockado |

---

## Arquitetura

A aplicação segue uma arquitetura em camadas com responsabilidades únicas (SRP) e injeção de dependências via construtor.

### Diagrama do fluxo de uma requisição

```
HTTP Request
    │
    ▼
┌─────────────────────────────────────────────┐
│  Controller (Blueprint Flask)               │
│  · parse HTTP (request.json / request.files)│
│  · delega ao Service                        │
│  · serializa resposta via Schema            │
│  · @handle_errors (boilerplate centralizado)│
└───────────────────┬─────────────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  Pydantic Schema │  ← valida e tipifica a entrada
         └────────┬─────────┘
                  │
                  ▼
    ┌─────────────────────────┐
    │       Service           │
    │  · regra de negócio     │
    │  · orquestração         │
    │  · @transactional       │
    └──┬──────────────────┬───┘
       │                  │
       ▼                  ▼
┌──────────────┐   ┌──────────────────┐
│  Repository  │   │  StorageClient   │
│  (SQLAlchemy)│   │  (S3 via boto3)  │
└──────┬───────┘   └──────────────────┘
       │
       ▼
  ┌─────────┐          ┌───────────────────┐
  │  Model  │          │ Strategy (padrão) │
  │  (ORM)  │          │ data mining       │
  └─────────┘          └───────────────────┘
```

### Responsabilidade de cada camada

| Camada | Responsabilidade |
|---|---|
| **Controller** | Recebe a requisição HTTP, chama o Service, devolve JSON. Não contém regra de negócio. |
| **Schema (Pydantic v2)** | Valida a entrada e serializa a saída. Única fonte de verdade de formato dos dados. |
| **Service** | Regra de negócio e orquestração de repositórios, storage e strategies. Decorado com `@transactional`. |
| **Repository** | Único ponto de contato com o SQLAlchemy. Isola as queries do resto do sistema. |
| **Model** | Declaração das tabelas ORM (Flask-SQLAlchemy). Sem lógica de negócio. |
| **StorageClient** | Encapsula boto3; responsável por upload/download/delete no S3. | 
| **Strategy** | Implementação de cada algoritmo de data mining (limpeza, normalização, redução, classificação). Registrado em `_REGISTRY`; selecionado por nome em tempo de execução. |
| **common/** | Erros de domínio, envelope de resposta, decorators (`@handle_errors`, `@transactional`), helpers de arquivos. |

---

## Estrutura de pastas

```
api/app/
├── __init__.py              # create_app(): wiring de extensões, serviços e blueprints
├── config.py                # Config / TestConfig (variáveis de ambiente)
├── extensions.py            # db, migrate, login_manager, cors (instâncias únicas)
│
├── controllers/             # Blueprints Flask — finos, sem regra de negócio
│   ├── auth_controller.py
│   ├── user_controller.py
│   ├── project_controller.py
│   ├── dataset_controller.py
│   └── data_mining/
│       ├── preprocessing_controller.py   # cleaning, normalization, reduction
│       ├── classification_controller.py
│       └── visualization_controller.py
│
├── schemas/                 # Pydantic v2 — validação e serialização
│   ├── auth.py
│   ├── user.py
│   ├── project.py
│   ├── dataset.py
│   └── data_mining/
│       ├── cleaning.py
│       ├── normalization.py
│       ├── reduction.py
│       ├── classification.py
│       └── visualization.py
│
├── services/                # Regra de negócio
│   ├── auth_service.py
│   ├── user_service.py
│   ├── project_service.py
│   ├── dataset_service.py
│   └── data_mining/
│       ├── cleaning_service.py
│       ├── normalization_service.py
│       ├── reduction_service.py
│       ├── classification_service.py
│       └── visualization_service.py
│
├── repositories/            # Acesso a dados (SQLAlchemy)
│   ├── base.py                    # BaseRepository com add/get/delete genéricos
│   ├── user_repository.py
│   ├── project_repository.py
│   ├── dataset_repository.py
│   └── clean_dataset_repository.py
│
├── models/                  # Modelos ORM (SQLAlchemy)
│   ├── user.py
│   ├── project.py
│   ├── dataset.py
│   └── clean_dataset.py
│
├── storage/
│   └── s3_client.py         # Encapsula boto3; init feito no create_app()
│
├── data_mining/             # Algoritmos (Strategy pattern)
│   ├── cleaning/
│   │   └── strategies.py    # MeanFillStrategy, MedianFillStrategy, ModeFillStrategy
│   ├── normalization/
│   │   └── strategies.py    # MinMaxStrategy, ZScoreStrategy
│   ├── reduction/
│   │   └── strategies.py    # PCAStrategy, RandomSamplingStrategy, SystematicSamplingStrategy
│   ├── classification/
│   │   └── strategies.py    # KNNStrategy
│   └── visualization/
│       └── measures.py      # Registros de medidas (tendência central, dispersão, forma, associação)
│
├── common/                  # Utilitários transversais
│   ├── errors.py            # DomainError, NotFoundError, UnauthorizedError, ValidationError, ExternalServiceError
│   ├── responses.py         # success_payload() / error_payload()
│   ├── decorators.py        # @handle_errors, @transactional
│   └── files.py             # bytes_to_mb_label e helpers de CSV
│
└── docs/
    └── openapi.py           # SWAGGER_CONFIG + build_swagger_template() para flasgger

tests/
├── conftest.py              # Fixtures: app, db, client, s3, auth_client
├── factories.py             # Fábricas de modelos para testes
└── integration/
    ├── test_auth.py
    ├── test_users.py
    ├── test_projects.py
    ├── test_datasets.py
    ├── test_cleaning.py
    ├── test_normalization.py
    ├── test_reduction.py
    ├── test_classification.py
    ├── test_visualization.py
    └── ...
```

---

## Fluxo de uma requisição

Exemplo concreto: `POST /api/datasets/create-dataset`

1. **HTTP chega** ao Blueprint `dataset_bp` (prefixo `/api/datasets`).
2. **`@login_required`** verifica a sessão; se inválida, retorna 401.
3. **`@handle_errors`** envolve o handler: captura `DomainError`, `PydanticValidationError` e exceções genéricas, sempre devolvendo o envelope padrão.
4. **Controller** lê o arquivo do `request.files` e valida o form com `DatasetCreateSchema.model_validate(request.form.to_dict())`. Qualquer campo inválido lança `PydanticValidationError`, capturado pelo decorator.
5. **`current_app.services["dataset"].create(data, csv_file, current_user.id)`** é chamado.
6. **Service (`DatasetService.create`)** — decorado com `@transactional`:
   - Valida extensão e tamanho do arquivo.
   - Verifica unicidade do nome (via `DatasetRepository`).
   - Verifica existência do projeto (via `ProjectRepository`).
   - Faz upload para o S3 via `StorageClient`.
   - Cria e persiste o objeto `Dataset` via `DatasetRepository.add()`.
   - `@transactional` faz `db.session.commit()` ao final; em caso de erro faz rollback e re-lança a exceção.
7. **Controller** serializa o retorno com `DatasetReadSchema.model_validate(dataset).model_dump()`.
8. **Resposta** é montada via `success_payload(...)` e devolvida como JSON com status 201.

---

## Convenções

### Envelope de resposta

Todas as respostas seguem o mesmo formato:

**Sucesso:**
```json
{
  "success": true,
  "message": "Operação realizada com sucesso!",
  "data": { ... }
}
```

**Erro:**
```json
{
  "success": false,
  "message": "Dados inválidos!",
  "errors": { "campo": ["mensagem de erro"] }
}
```

As funções `success_payload()` e `error_payload()` em `app/common/responses.py` constroem esses dicionários.

### `@handle_errors` (controllers)

Decorator aplicado em todos os handlers. Centraliza o tratamento de exceções:

- `DomainError` (e subclasses) → resposta com `exc.status` e `exc.details`.
- `PydanticValidationError` → 422 com mapeamento `{campo: [mensagens]}`.
- Qualquer outra exceção → 500, rollback da sessão, log de exceção.

### `@transactional` (services)

Decorator aplicado em métodos de escrita nos serviços. Faz `db.session.commit()` ao final e `db.session.rollback()` em caso de qualquer exceção antes de re-lançá-la.

### Validação com Pydantic v2

Schemas herdam de `pydantic.BaseModel`. Schemas de leitura usam `model_config = ConfigDict(from_attributes=True)` para desserializar modelos ORM diretamente. A validação é sempre iniciada com `Schema.model_validate(...)`.

### Repositórios

Todos herdam de `BaseRepository` (que provê `add`, `get`, `delete` genéricos). Repositórios específicos adicionam queries de domínio (ex.: `list_by_user`, `get_owned`, `name_taken`). Nenhuma outra camada acessa `db.session` diretamente.

---

## Como estender

### (a) Adicionar um novo domínio CRUD

1. **Schema** — crie `api/app/schemas/meu_dominio.py` com as classes Pydantic de entrada e saída.
2. **Model** — crie `api/app/models/meu_dominio.py` com o modelo SQLAlchemy e registre em `api/app/models/__init__.py`.
3. **Repository** — crie `api/app/repositories/meu_dominio_repository.py` herdando de `BaseRepository`.
4. **Service** — crie `api/app/services/meu_dominio_service.py` recebendo o repositório e dependências via construtor.
5. **Controller** — crie `api/app/controllers/meu_dominio_controller.py` com um Blueprint; aplique `@login_required` e `@handle_errors` em cada handler.
6. **Registre** em `wire_services(app)` em `api/app/__init__.py`:
   ```python
   from app.repositories.meu_dominio_repository import MeuDominioRepository
   from app.services.meu_dominio_service import MeuDominioService
   # ...
   meu_dominio = MeuDominioRepository(session)
   services["meu_dominio"] = MeuDominioService(meu_dominio)
   ```
7. **Registre** o blueprint em `register_controllers(app)` em `api/app/controllers/__init__.py`:
   ```python
   from app.controllers.meu_dominio_controller import meu_dominio_bp
   app.register_blueprint(meu_dominio_bp, url_prefix="/api/meu-dominio")
   ```

### (b) Adicionar uma nova Strategy de data mining

1. Crie a classe em `api/app/data_mining/<area>/strategies.py` herdando da classe abstrata da área:
   ```python
   class MinhaStrategy(MissingValueStrategy):  # ou NormalizationStrategy, ReductionStrategy, etc.
       name = "minha_tecnica"

       def apply(self, series: pd.Series) -> pd.Series:
           # implementação
           ...
   ```
2. Registre no `_REGISTRY` do mesmo arquivo:
   ```python
   _REGISTRY = {s.name: s for s in (..., MinhaStrategy)}
   ```

Nenhum outro arquivo precisa ser alterado (princípio Open/Closed).

---

## Endpoints

### `/api/auth`
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/auth/login` | Realiza login (retorna dados do usuário na sessão) |
| `POST` | `/api/auth/logout` | Encerra a sessão |
| `GET` | `/api/auth/me` | Retorna os dados do usuário autenticado |

### `/api/users`
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/users/` | Cria um novo usuário |
| `PUT` | `/api/users/` | Atualiza dados do usuário autenticado |
| `DELETE` | `/api/users/` | Remove o usuário autenticado |

### `/api/projects`
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/projects/` | Lista projetos do usuário |
| `GET` | `/api/projects/<id>` | Retorna um projeto com seus datasets |
| `POST` | `/api/projects/` | Cria um projeto |
| `PUT` | `/api/projects/<id>` | Atualiza um projeto |
| `DELETE` | `/api/projects/<id>` | Remove um projeto |

### `/api/datasets`
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/datasets/` | Lista bases de dados do usuário |
| `GET` | `/api/datasets/<id>` | Retorna uma base de dados |
| `POST` | `/api/datasets/create-dataset` | Cria uma base de dados (upload CSV via multipart) |
| `PUT` | `/api/datasets/<id>` | Atualiza uma base de dados |
| `DELETE` | `/api/datasets/<id>` | Remove uma base de dados |

### `/api/preprocessing`
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/preprocessing/data-cleaning/<dataset_id>` | Limpeza de dados (preenchimento de valores faltantes) |
| `POST` | `/api/preprocessing/data-normalization/<dataset_id>` | Normalização de dados |
| `POST` | `/api/preprocessing/data-reduction/<dataset_id>` | Redução de dados |

Strategies disponíveis por operação:
- **Limpeza:** `media`, `mediana`, `moda`
- **Normalização:** `minmax`, `zscore`
- **Redução:** `pca`, `amostragem_aleatoria`, `amostragem_sistematica`

### `/api/classification`
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/classification/<dataset_id>` | Executa algoritmo de classificação (ex.: `knn`) |

### `/api/data-visualization`
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/data-visualization/measure-central-tendency/<dataset_id>` | Medidas de tendência central |
| `POST` | `/api/data-visualization/dispersion-measure/<dataset_id>` | Medidas de dispersão |
| `POST` | `/api/data-visualization/shape-measure/<dataset_id>` | Medidas de forma |
| `POST` | `/api/data-visualization/association-measure/<dataset_id>` | Medidas de associação |

---

## Instalação

1. Clone o repositório:
   ```sh
   git clone https://github.com/seu-usuario/EasyMinerAPI.git
   cd EasyMinerAPI
   ```

2. Crie e ative o ambiente virtual:
   ```sh
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Instale as dependências:
   ```sh
   pip install -r requirements.txt
   ```

4. Configure as variáveis de ambiente:
   ```sh
   export SECRET_KEY=sua_chave_secreta
   export SQLALCHEMY_DATABASE_URI=sua_uri_do_banco
   export S3_BUCKET=seu_bucket_s3
   export S3_KEY=sua_chave_s3
   export S3_SECRET=seu_segredo_s3
   ```

5. Execute as migrações e inicie a aplicação:
   ```sh
   flask --app wsgi db upgrade
   flask --app wsgi run
   ```

A rota raiz (`GET /`) confirma que a API está no ar e indica o endereço da documentação.

---

## Testes

Os testes são de integração por endpoint. Rodam com banco SQLite em memória (recriado por teste) e S3 mockado via `moto`.

```sh
./venv/bin/python -m pytest
```

Fixtures disponíveis em `tests/conftest.py`:

| Fixture | O que faz |
|---|---|
| `app` | Cria a aplicação com `TestConfig`, sobe o banco em memória e derruba ao final. |
| `db` | Referência à instância do SQLAlchemy. |
| `client` | Flask test client sem autenticação. |
| `s3` | Mock AWS S3 via `moto` com um bucket de teste criado. |
| `auth_client` | Cria um usuário via fábrica, faz login e retorna `(client, user)` já autenticados. |

Cada endpoint tem, no mínimo, testes para: sucesso (200/201), não autenticado (401), recurso inexistente (404) e payload inválido (422).

---

## Documentação da API

O Swagger UI é gerado automaticamente em tempo de execução a partir das docstrings dos controllers (flasgger).

- **Swagger UI interativo:** [https://easyminerapi.fly.dev/apidocs](https://easyminerapi.fly.dev/apidocs) (ou `/apidocs/` em ambiente local)
- **Spec OpenAPI (JSON):** `/apispec.json`

---
