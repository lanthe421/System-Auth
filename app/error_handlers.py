"""Global exception handlers for the Auth System API.

This module provides consistent error response formatting across all endpoints.

Requirements: 1.2, 2.2, 2.3, 4.2, 8.2, 8.3, 9.5
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError

from app.exceptions import (
    AuthSystemException,
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ConflictError,
    NotFoundError
)


def create_error_response(
    code: str,
    message: str,
    details: dict = None,
    status_code: int = 500
) -> JSONResponse:
    """
    Create a consistent error response.
    
    Args:
        code: Error code identifier
        message: Human-readable error message
        details: Additional error details
        status_code: HTTP status code
        
    Returns:
        JSONResponse with consistent error format
    """
    error_content = {
        "error": {
            "code": code,
            "message": message
        }
    }
    
    if details:
        error_content["error"]["details"] = details
    
    return JSONResponse(
        status_code=status_code,
        content=error_content
    )


async def authentication_error_handler(
    request: Request,
    exc: AuthenticationError
) -> JSONResponse:
    """
    Handle authentication errors (401).
    
    Requirements: 2.2, 2.3, 8.3
    """
    return create_error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_401_UNAUTHORIZED
    )


async def authorization_error_handler(
    request: Request,
    exc: AuthorizationError
) -> JSONResponse:
    """
    Handle authorization errors (403).
    
    Requirements: 8.2, 9.5
    """
    return create_error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_403_FORBIDDEN
    )


async def validation_error_handler(
    request: Request,
    exc: ValidationError
) -> JSONResponse:
    """
    Handle validation errors (422).
    
    Requirements: 1.2, 1.3
    """
    return create_error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def conflict_error_handler(
    request: Request,
    exc: ConflictError
) -> JSONResponse:
    """
    Handle conflict errors (409).
    
    Requirements: 1.2, 4.2
    """
    return create_error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_409_CONFLICT
    )


async def not_found_error_handler(
    request: Request,
    exc: NotFoundError
) -> JSONResponse:
    """
    Handle not found errors (404).
    
    Requirements: 9.5
    """
    return create_error_response(
        code=exc.code,
        message=exc.message,
        details=exc.details,
        status_code=status.HTTP_404_NOT_FOUND
    )


async def request_validation_error_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """
    Handle FastAPI request validation errors (422).
    
    This handles Pydantic validation errors from request bodies.
    
    Requirements: 1.2, 1.3
    """
    # Extract validation error details
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"] if loc != "body")
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return create_error_response(
        code="VALIDATION_ERROR",
        message="Request validation failed",
        details={"errors": errors},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def pydantic_validation_error_handler(
    request: Request,
    exc: PydanticValidationError
) -> JSONResponse:
    """
    Handle Pydantic validation errors (422).
    
    Requirements: 1.2, 1.3
    """
    # Extract validation error details
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    return create_error_response(
        code="VALIDATION_ERROR",
        message="Validation failed",
        details={"errors": errors},
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )


async def integrity_error_handler(
    request: Request,
    exc: IntegrityError
) -> JSONResponse:
    """
    Handle database integrity errors (409).
    
    This typically occurs with unique constraint violations.
    
    Requirements: 1.2, 4.2
    """
    error_message = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    
    # Try to extract meaningful information from the error
    details = {}
    if "unique" in error_message.lower() or "duplicate" in error_message.lower():
        details["reason"] = "A record with this value already exists"
    
    return create_error_response(
        code="CONFLICT",
        message="Database constraint violation",
        details=details,
        status_code=status.HTTP_409_CONFLICT
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception
) -> JSONResponse:
    """
    Handle any unhandled exceptions (500).
    
    This is a catch-all handler for unexpected errors.
    """
    # Log the exception for debugging (in production, use proper logging)
    import traceback
    traceback.print_exc()
    
    return create_error_response(
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred",
        details={},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def register_exception_handlers(app):
    """
    Register all exception handlers with the FastAPI application.
    
    Args:
        app: FastAPI application instance
    """
    # Custom exception handlers
    app.add_exception_handler(AuthenticationError, authentication_error_handler)
    app.add_exception_handler(AuthorizationError, authorization_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(ConflictError, conflict_error_handler)
    app.add_exception_handler(NotFoundError, not_found_error_handler)
    
    # FastAPI/Pydantic validation errors
    app.add_exception_handler(RequestValidationError, request_validation_error_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_error_handler)
    
    # Database errors
    app.add_exception_handler(IntegrityError, integrity_error_handler)
    
    # Generic exception handler (catch-all)
    app.add_exception_handler(Exception, generic_exception_handler)
