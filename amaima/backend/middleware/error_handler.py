# backend/middleware/error_handler.py

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import BaseModel
import logging
from datetime import datetime
from typing import List, Optional

logger = logging.getLogger(__name__)


class ValidationErrorDetail(BaseModel):
    field: str
    message: str
    type: str


class ApiError(BaseModel):
    code: str
    message: str
    type: str
    details: Optional[List[ValidationErrorDetail]] = None


class ErrorResponse(BaseModel):
    error: ApiError
    meta: dict


class ErrorHandler:
    """Centralized error handler for the API"""
    
    ERROR_CODES = {
        400: "BAD_REQUEST",
        401: "AUTH_TOKEN_INVALID",
        403: "AUTH_PERMISSION_DENIED",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        429: "SYSTEM_RATE_LIMITED",
        500: "SYSTEM_INTERNAL_ERROR",
        503: "SYSTEM_UNAVAILABLE",
    }
    
    def __init__(self):
        self.exception_handlers: dict = {}
    
    async def handle_exception(
        self,
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Main exception handler"""
        
        request_id = request.state.request_id if hasattr(request.state, 'request_id') else ""
        
        if isinstance(exc, StarletteHTTPException):
            return await self.handle_http_exception(request, exc, request_id)
        
        if isinstance(exc, RequestValidationError):
            return await self.handle_validation_error(request, exc, request_id)
        
        if isinstance(exc, ApiException):
            return await self.handle_api_exception(request, exc, request_id)
        
        return await self.handle_generic_error(request, exc, request_id)
    
    async def handle_http_exception(
        self,
        request: Request,
        exc: StarletteHTTPException,
        request_id: str
    ) -> JSONResponse:
        code = self.ERROR_CODES.get(
            exc.status_code,
            f"HTTP_{exc.status_code}"
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": code,
                    "message": exc.detail,
                    "type": "http_error"
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )
    
    async def handle_validation_error(
        self,
        request: Request,
        exc: RequestValidationError,
        request_id: str
    ) -> JSONResponse:
        errors = []
        
        for error in exc.errors():
            errors.append(ValidationErrorDetail(
                field=" -> ".join(str(loc) for loc in error["loc"]),
                message=error["msg"],
                type=error["type"]
            ))
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "type": "validation_error",
                    "details": [e.dict() for e in errors]
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )
    
    async def handle_api_exception(
        self,
        request: Request,
        exc: "ApiException",
        request_id: str
    ) -> JSONResponse:
        logger.warning(
            f"API error: {exc.code} - {exc.message}",
            extra={"request_id": request_id, "code": exc.code}
        )
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "type": exc.error_type,
                    "details": [e.dict() for e in exc.details] if exc.details else None
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )
    
    async def handle_generic_error(
        self,
        request: Request,
        exc: Exception,
        request_id: str
    ) -> JSONResponse:
        logger.error(
            f"Unhandled exception: {exc}",
            exc_info=True,
            extra={"request_id": request_id}
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "SYSTEM_INTERNAL_ERROR",
                    "message": "An internal error occurred",
                    "type": "server_error"
                },
                "meta": {
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "path": str(request.url.path)
                }
            }
        )


# Custom exception class
class ApiException(Exception):
    """Custom exception for API errors"""
    
    def __init__(
        self,
        code: str,
        message: str,
        error_type: str = "api_error",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Optional[List[ValidationErrorDetail]] = None
    ):
        self.code = code
        self.message = message
        self.error_type = error_type
        self.status_code = status_code
        self.details = details
        super().__init__(message)
