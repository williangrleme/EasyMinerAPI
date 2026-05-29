# EasyMinerAPI Refactor — Handoff (2026-05-29)

Execution of `docs/superpowers/plans/2026-05-27-easyminer-refactor.md` via subagent-driven
development (implementer + review per task), working directly on branch `develop`.

## Status: T1–T10 of 17 done. NOT pushed yet.

- **Working tree:** clean (all work committed).
- **Tests:** `./venv/bin/python -m pytest -q` → **50 passed** at last run.
- **NOT pushed** to origin (push is T17, not reached). Do not push until history is verified — see Caveat below.

## Environment (important)
- A virtualenv with all deps lives at `./venv/` (gitignored). Run everything through it:
  `./venv/bin/python -m pytest -q`. `pytest.ini` sets `pythonpath = api`.
- pip was bootstrapped via get-pip.py (system lacked `python3.12-venv`). Deps installed:
  current `requirements.txt` + `pydantic[email]==2.9.2 pytest==8.3.3 pytest-flask==1.3.0 moto[s3]==5.0.18`.
  (requirements.txt itself is updated in T15 — not yet done.)
- Git identity isn't global; commit with
  `git -c user.name="Willian Leme" -c user.email="53802750+williangrleme@users.noreply.github.com" ...`

## Done (each TDD, committed)
- **T1** common/ (errors, responses envelope, `handle_errors`/`transactional` decorators, files helpers)
- **T2** test infra (conftest fixtures app/db/client/s3-moto/auth_client, factories, `TestConfig`); dropped CSRF/swagger from extensions; factory accepts config
- **T3** `storage/s3_client.py` `StorageClient`
- **T4** repositories (base + user/project/dataset/clean_dataset)
- **T4.5** (coordinator-authored) app-factory skeleton: `create_app` → `wire_services` + `register_controllers`; removed `CleanDataset` S3 `after_delete` listener; fixed `user.py` import. Wiring convention: services in a dict literal in `wire_services`, blueprints in `register_controllers`.
- **T5** auth (LoginSchema, AuthService, auth_bp /api/auth: login/logout/me) + JSON 401 unauthorized_handler
- **T6** users (Create/Update schemas, UserService, /api/users POST public, PUT/DELETE login)
- **T7** projects (/api/projects CRUD, ProjectDetailSchema with nested datasets)
- **T8** datasets (multipart upload, /api/datasets, create-dataset). Review-fix applied: update() now enforces name-uniqueness + project-ownership; `_validate_file` guards None filename.
- **T9** data cleaning (Strategy: media/mediana/moda) /api/preprocessing/data-cleaning. Review-fix: ModeFillStrategy guards empty mode (422 not 500).
- **T10** data normalization (Strategy: minmax/zscore) /api/preprocessing/data-normalization. Review-fix: non-numeric column → 422 (numeric-dtype guard).

## Remaining
- **T11** data reduction (Strategy: pca/amostragem_aleatoria/amostragem_sistematica) — add route to `preprocessing_controller.py`, wire `services["reduction"]`. Plan has full code.
- **T12** classification (KNN Strategy) — new `classification_controller.py` (classification_bp /api/classification), register in `controllers/__init__.py`, wire `services["classification"]`.
- **T13** visualization — port measures from old `data_visualization_controller.py` into `data_mining/visualization/measures.py` (4 registries), new visualization_controller.py (/api/data-visualization, 4 routes), wire `services["visualization"]`.
- **T14** remove old code: `api/app/routes/`, `api/app/forms/`, `api/app/response_handlers.py`, `api/app/controllers/s3_controller.py`, `api/app/controllers/data_mining/preprocessing/` (old), old `data_visualization_controller.py`, `api/app/swagger/`. Then run full suite.
- **T15** update `requirements.txt` (remove Flask-WTF/WTForms; add pydantic/pytest/moto/flasgger stays); Swagger generated from Pydantic schemas (`docs/openapi.py`); add docstrings; expose /apidocs.
- **T16** rewrite README (new architecture, how to add a domain / a Strategy, how to run tests, env vars, contract changes).
- **T17** full suite green + app boots + `grep` for old imports + `git push origin develop`.

## Pattern for the remaining data-mining tasks (T11–T13)
Each: create `data_mining/<x>/strategies.py` (or measures.py) + `schemas/data_mining/<x>.py` +
`services/data_mining/<x>_service.py`; the service imports `read_csv` from `app.common.files`
as a module global (tests monkeypatch it); add route(s) to the controller; add an entry to the
`services` dict in `api/app/__init__.py` `wire_services` and (T12/T13) a blueprint in
`controllers/__init__.py`. Tests in `tests/integration/test_<x>.py`.

## Deliberately deferred review findings (decide later; surfaced to the user)
- **Apply the non-numeric-column → 422 guard to T11 (reduction) and T12 (classification)** too,
  for consistency with T10 (otherwise a text column selected for PCA/KNN yields a 500).
- Email/name case-normalization not done (prod DB is MySQL, default case-insensitive collation).
- S3-vs-DB atomicity on delete: if an S3 delete fails mid-loop, DB rolls back but earlier S3
  files are already gone (orphans). Pre-existing behavior; acceptable edge case.
- Cleaning `_MISSING_MAP["0"]=0` (int) won't match string "0" in object-dtype columns
  (preserved-from-original; numeric columns work).

## ⚠️ Caveat — verify git history before pushing (T17)
During wrap-up the `git log` output appeared scrambled/duplicated (possibly a display artifact,
possibly tangled by repeated `--amend`). The **working tree is clean and 50 tests pass**, so the
*code* is the source of truth and is healthy. Before T17 push, run `git log --graph --oneline`
and confirm a sane linear chain on `develop` (T1→T10). If commits are duplicated/tangled, consider
a soft cleanup (e.g. interactive rebase or `git reset --soft` to the plan commit `3b4032c` and
re-commit the working tree in logical chunks) — the tree contents are correct either way.
