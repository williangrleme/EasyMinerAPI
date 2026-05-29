# EasyMinerAPI Refactor — Notas de Conclusão (2026-05-29)

Execução do plano `docs/superpowers/plans/2026-05-27-easyminer-refactor.md` via
subagent-driven development (implementer + revisão por tarefa), direto na branch `develop`.

## Status: TODAS as 17 tarefas concluídas (T1–T17). Branch `develop` enviada ao origin.

- **Working tree:** limpa.
- **Testes:** `./venv/bin/python -m pytest -q` → **68 passed**.
- **App sobe**, Swagger em `/apidocs/` gerado dos schemas Pydantic, código antigo removido.
- Arquitetura documentada no `README.md` (fonte canônica). Este arquivo guarda só notas de processo.

## O que foi feito
Camadas: `common/` (erros, envelope, decorators `handle_errors`/`transactional`, helpers) →
`schemas/` (Pydantic v2) → `controllers/` (blueprints finos) → `services/` (regra + `@transactional`)
→ `repositories/` (único ponto SQLAlchemy) → `models/`. `StorageClient` para S3; Strategy pattern
para data mining (cleaning/normalization/reduction/classification) + registries de medidas
(visualization). Wiring em `wire_services`/`register_controllers`. WTForms/CSRF/`swagger.yaml`
estático e camadas `routes/`+`forms/` removidos.

## Ambiente
- Virtualenv em `./venv/` (gitignored) com todas as deps. Rodar via `./venv/bin/python -m pytest`.
  A máquina não tinha `pip`/`python3.12-venv`; o pip foi bootstrapado com get-pip.py. Para deploy
  real, instalar `python3.12-venv` adequadamente. `requirements.txt` já atualizado (sem WTForms;
  com pydantic[email]/pytest/pytest-flask/moto).

## Follow-ups deliberadamente deferidos (decisão do dono)
- **Coluna não numérica → 500** ainda é possível em alguns caminhos de visualization (as funções de
  medida foram portadas 1:1 do código original). Normalização, PCA e KNN já tratam isso como 422.
- **Atomicidade S3 × banco no delete:** se um `storage.delete` falhar no meio do loop, o banco faz
  rollback mas arquivos S3 já apagados ficam órfãos. Comportamento pré-existente; aceitável.
- **Normalização de caixa de e-mail/nome** não feita (o banco de produção é MySQL, colação
  case-insensitive por padrão, então a unicidade já cobre o caso comum).
- **Cleaning `_MISSING_MAP["0"]=0` (int)** não casa a string `"0"` em colunas object-dtype
  (preservado do comportamento original; colunas numéricas funcionam).
