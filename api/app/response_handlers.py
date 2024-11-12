import json

from flask import Response, current_app
from werkzeug.exceptions import HTTPException

HTTP_ERROR_MESSAGES = {
    401: "Não autorizado!",
    404: "Não encontrado!",
    422: "Dados inválidos!",
    500: "Erro interno do servidor!",
}


def log_error(message, error):
    current_app.logger.error(f"{message}: {str(error)}")


def create_response(message, success, data=None, status_code=200):
    response_data = {
        "message": message,
        "success": success,
        "data": data,
    }
    return Response(
        json.dumps(response_data),
        mimetype="application/json",
        status=status_code,
    )


def format_error(error):
    if isinstance(error, HTTPException):
        error = error.description
    return str(error)


def handle_unprocessable_entity(errors=None):
    return create_response(
        HTTP_ERROR_MESSAGES[422],
        data=errors,
        success=False,
        status_code=422,
    )


def handle_success(message="Operação bem sucedida!", data=None):
    return create_response(
        message,
        success=True,
        data=data,
        status_code=200,
    )


def handle_internal_server_error_response(error=None, message=HTTP_ERROR_MESSAGES[500]):
    log_error(message, error)
    return create_response(
        message,
        success=False,
        data=format_error(error),
        status_code=500,
    )


def handle_not_found_response(error=None, message=HTTP_ERROR_MESSAGES[404]):
    return create_response(
        message,
        success=False,
        data=format_error(error),
        status_code=404,
    )


def handle_not_authorized_response(message=HTTP_ERROR_MESSAGES[401]):
    return create_response(
        message,
        success=False,
        status_code=401,
    )


def register_response_errors(app):
    @app.errorhandler(401)
    def handle_auth_error(e):
        return handle_not_authorized_response()

    @app.errorhandler(500)
    def handle_internal_server_error(e):
        return handle_internal_server_error_response(e)

    @app.errorhandler(422)
    def handle_unprocessable_entity_error(e):
        return handle_unprocessable_entity(e)

    @app.errorhandler(404)
    def handle_not_found_error(e):
        return handle_not_found_response(e)

    @app.errorhandler(Exception)
    def handle_generic_error(e):
        return handle_internal_server_error_response(e)
