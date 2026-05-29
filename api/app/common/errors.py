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
