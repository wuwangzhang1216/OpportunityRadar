"""Custom exceptions for the application."""

from typing import Any, Optional


class AppException(Exception):
    """Base exception for the application."""

    def __init__(
        self,
        message: str = "An error occurred",
        status_code: int = 500,
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class UnauthorizedException(AppException):
    """Exception for unauthorized access."""

    def __init__(self, message: str = "Unauthorized", details: Optional[dict[str, Any]] = None):
        super().__init__(message=message, status_code=401, details=details)


class ForbiddenException(AppException):
    """Exception for forbidden access."""

    def __init__(self, message: str = "Forbidden", details: Optional[dict[str, Any]] = None):
        super().__init__(message=message, status_code=403, details=details)


class NotFoundException(AppException):
    """Exception for resource not found."""

    def __init__(self, message: str = "Not found", details: Optional[dict[str, Any]] = None):
        super().__init__(message=message, status_code=404, details=details)


class BadRequestException(AppException):
    """Exception for bad request."""

    def __init__(self, message: str = "Bad request", details: Optional[dict[str, Any]] = None):
        super().__init__(message=message, status_code=400, details=details)


class ConflictException(AppException):
    """Exception for resource conflict."""

    def __init__(
        self, message: str = "Resource already exists", details: Optional[dict[str, Any]] = None
    ):
        super().__init__(message=message, status_code=409, details=details)
