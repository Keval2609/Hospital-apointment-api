"""
Custom application exceptions.

Each exception carries an HTTP status code, a machine-readable error_code
string, and a human-readable detail message.  The global exception handlers
in ``exception_handlers.py`` convert these into consistent JSON responses.
"""


class AppException(Exception):
    """Base exception for all application-level errors."""

    def __init__(
        self,
        status_code: int = 500,
        detail: str = "An unexpected error occurred.",
        error_code: str = "INTERNAL_ERROR",
    ) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code
        super().__init__(detail)


class NotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, detail: str = "Resource not found.") -> None:
        super().__init__(status_code=404, detail=detail, error_code="NOT_FOUND")


class UnauthorizedException(AppException):
    """Raised when authentication is missing or invalid."""

    def __init__(self, detail: str = "Could not validate credentials.") -> None:
        super().__init__(
            status_code=401, detail=detail, error_code="UNAUTHORIZED"
        )


class ForbiddenException(AppException):
    """Raised when the user lacks the required permissions."""

    def __init__(self, detail: str = "You do not have permission to perform this action.") -> None:
        super().__init__(status_code=403, detail=detail, error_code="FORBIDDEN")


class ConflictException(AppException):
    """Raised when a unique constraint would be violated."""

    def __init__(self, detail: str = "Resource already exists.") -> None:
        super().__init__(status_code=409, detail=detail, error_code="CONFLICT")


class ValidationException(AppException):
    """Raised when business-logic validation fails."""

    def __init__(self, detail: str = "Validation error.") -> None:
        super().__init__(
            status_code=422, detail=detail, error_code="VALIDATION_ERROR"
        )
