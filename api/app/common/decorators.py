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
