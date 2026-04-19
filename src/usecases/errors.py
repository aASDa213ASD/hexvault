from __future__ import annotations


class UseCaseError(Exception):
    """Base class for application-layer errors."""


class NotFoundError(UseCaseError):
    pass


class ValidationError(UseCaseError):
    pass


class ConflictError(UseCaseError):
    def __init__(self, message: str, payload: object | None = None) -> None:
        super().__init__(message)
        self.payload = payload


class ExternalUnavailableError(UseCaseError):
    pass


class ExternalRequestError(UseCaseError):
    pass
