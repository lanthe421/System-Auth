"""Custom exceptions and error handling for the Auth System."""

from typing import Optional, Dict, Any


class AuthSystemException(Exception):
    """Base exception for all Auth System errors."""
    
    def __init__(
        self,
        message: str,
        code: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AuthSystemException):
    """Raised when authentication fails (401)."""
    
    def __init__(
        self,
        message: str = "Authentication failed",
        code: str = "AUTHENTICATION_FAILED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class AuthorizationError(AuthSystemException):
    """Raised when authorization fails (403)."""
    
    def __init__(
        self,
        message: str = "Access forbidden",
        code: str = "AUTHORIZATION_FAILED",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class ValidationError(AuthSystemException):
    """Raised when validation fails (422)."""
    
    def __init__(
        self,
        message: str = "Validation failed",
        code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class ConflictError(AuthSystemException):
    """Raised when a resource conflict occurs (409)."""
    
    def __init__(
        self,
        message: str = "Resource conflict",
        code: str = "CONFLICT",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)


class NotFoundError(AuthSystemException):
    """Raised when a resource is not found (404)."""
    
    def __init__(
        self,
        message: str = "Resource not found",
        code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, code, details)
