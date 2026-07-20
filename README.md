# EasyMinerAPI

Back-end do EasyMiner, uma ferramenta de KDD (Knowledge Discovery in Databases). É uma API REST em Flask onde o usuário cria projetos, sobe bases de dados em CSV e executa sobre elas algoritmos de pré-processamento (limpeza, normalização, redução), classificação e medidas estatísticas.

## Stack

- Flask 3, Flask-SQLAlchemy e Flask-Migrate (Postgres em produção, SQLite nos testes)
- Flask-Login para autenticação por sessão (cookie)
- Pydantic v2 para validação de entrada e serialização de saída
- pandas e scikit-learn nos algoritmos de mineração
- boto3 — os CSVs ficam num bucket S3, não em disco
- flasgger gera o Swagger UI em `/apidocs/` a partir das docstrings dos controllers

## Como o código está organizado

O fluxo de uma requisição é controller → service → repository. O controller (Blueprint) só faz parse do HTTP e serializa a resposta; a regra de negócio fica no service; o repository é o único ponto que toca o SQLAlchemy. Os algoritmos de mineração são classes Strategy registradas por nome em `api/app/data_mining/` — pra adicionar uma técnica nova basta criar a classe e registrá-la no `_REGISTRY` do módulo.

Todas as respostas usam o mesmo envelope:

```json
{ "success": true, "message": "...", "data": { } }
{ "success": false, "message": "...", "errors": { "campo": ["mensagem"] } }
```

## Endpoints

| Rota | O que faz |
|---|---|
| `POST /api/users/` | cria usuário |
| `POST /api/auth/login` · `/logout` · `GET /me` | sessão |
| `GET/POST/PUT/DELETE /api/projects/` | CRUD de projetos |
| `GET/PUT/DELETE /api/datasets/` · `POST /api/datasets/create-dataset` | CRUD de bases (upload CSV multipart, campo `csv_file`) |
| `POST /api/preprocessing/data-cleaning/<id>` | preenche valores faltantes (`media`, `mediana`, `moda`) |
| `POST /api/preprocessing/data-normalization/<id>` | `minmax`, `zscore` |
| `POST /api/preprocessing/data-reduction/<id>` | `pca`, `amostragem_aleatoria`, `amostragem_sistematica` |
| `POST /api/classification/<id>` | KNN |
| `POST /api/data-visualization/<medida>/<id>` | tendência central, dispersão, forma, associação |

O detalhe de cada payload está no Swagger: `/apidocs/` local ou [easyminerapi.fly.dev/apidocs](https://easyminerapi.fly.dev/apidocs).

## Rodando localmente

```sh
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export SECRET_KEY=qualquer-coisa
export SQLALCHEMY_DATABASE_URI=sqlite:///dev.db
export S3_BUCKET=seu-bucket
export S3_KEY=...
export S3_SECRET=...

flask --app wsgi db upgrade
flask --app wsgi run
```

Dois pontos de atenção:

- O upload/download de CSV usa S3 de verdade — sem credenciais válidas, os endpoints de dataset e mineração não funcionam (os testes não precisam, usam mock).
- `api/app/config.py` marca o cookie de sessão com `Secure` (pensado pro deploy atrás de HTTPS). Pra logar via `curl` em `http://localhost`, troque `SESSION_COOKIE_SECURE` para `False` enquanto desenvolve.

## Testes

```sh
python -m pytest
```

São testes de integração por endpoint, com SQLite em memória e S3 mockado via `moto`. Não precisam de nenhuma variável de ambiente nem serviço externo.

## Exemplo: Pima Indians Diabetes

Um bom dataset pra testar o fluxo inteiro é o [Pima Indians Diabetes](https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database) (`diabetes.csv`): 768 linhas, colunas numéricas e uma coluna binária `Outcome` que serve de target pra classificação.

```sh
# usuário + login (cookie fica no cookies.txt)
curl -s -X POST http://localhost:5000/api/users/ -H 'Content-Type: application/json' \
  -d '{"name": "Usuario de Teste", "phone_number": "11999999999", "email": "teste@teste.com", "password": "senha12345"}'

curl -s -c cookies.txt -X POST http://localhost:5000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email": "teste@teste.com", "password": "senha12345"}'

# projeto + upload do CSV
curl -s -b cookies.txt -X POST http://localhost:5000/api/projects/ -H 'Content-Type: application/json' \
  -d '{"name": "Diabetes", "description": "Testes com o dataset Pima"}'

curl -s -b cookies.txt -X POST http://localhost:5000/api/datasets/create-dataset \
  -F name=diabetes -F project_id=1 -F csv_file=@diabetes.csv
```

No Pima, valores faltantes vêm codificados como `0` em colunas onde zero não faz sentido (glicose, pressão, IMC). A limpeza abaixo troca esses zeros pela mediana; depois a classificação roda um KNN prevendo `Outcome`:

```sh
curl -s -b cookies.txt -X POST http://localhost:5000/api/preprocessing/data-cleaning/1 \
  -H 'Content-Type: application/json' \
  -d '{"features": ["Glucose", "BloodPressure", "BMI"], "methods": "mediana", "missing_values": ["0"]}'

curl -s -b cookies.txt -X POST http://localhost:5000/api/classification/1 \
  -H 'Content-Type: application/json' \
  -d '{"features": ["Glucose", "BMI", "Age"], "target": "Outcome", "k_neighbors": 5, "use_clean_dataset": true}'
```

A resposta da classificação traz acurácia e as métricas do modelo; a da limpeza, a URL do CSV limpo gerado no S3.
