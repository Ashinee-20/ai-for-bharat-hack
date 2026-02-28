"""Custom exception classes for error handling."""

from typing import Any, Dict, Optional
from datetime import datetime


class AgriBridgeError(Exception):
    """Base exception for all AgriBridge errors."""

    def __init__(
        self,
        message: str,
        code: str,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 500,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = datetime.utcnow()

    def to_dict(self, request_id: Optional[str] = None) -> Dict[str, Any]:
        """Convert exception to error response dictionary."""
        error_dict = {
            "error": {
                "code": self.code,
                "message": self.message,
                "timestamp": self.timestamp.isoformat() + "Z",
            }
        }
        
        if self.details:
            error_dict["error"]["details"] = self.details
            
        if request_id:
            error_dict["error"]["requestId"] = request_id
            
        return error_dict


class ValidationError(AgriBridgeError):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="VALIDATION_ERROR",
            details=details,
            status_code=400,
        )


class AuthenticationError(AgriBridgeError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            code="AUTHENTICATION_ERROR",
            status_code=401,
        )


class AuthorizationError(AgriBridgeError):
    """Raised when authorization fails."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            code="AUTHORIZATION_ERROR",
            status_code=403,
        )


class NotFoundError(AgriBridgeError):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            message=f"{resource} not found: {identifier}",
            code="NOT_FOUND",
            details={"resource": resource, "identifier": identifier},
            status_code=404,
        )


class ExternalServiceError(AgriBridgeError):
    """Raised when an external service call fails."""

    def __init__(
        self,
        service: str,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(
            message=f"{service}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, **(details or {})},
            status_code=502,
        )


class RateLimitError(AgriBridgeError):
    """Raised when rate limit is exceeded."""

    def __init__(self, limit: int, window: str):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window": window},
            status_code=429,
        )


class DataIntegrityError(AgriBridgeError):
    """Raised when data integrity constraints are violated."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="DATA_INTEGRITY_ERROR",
            details=details,
            status_code=409,
        )
