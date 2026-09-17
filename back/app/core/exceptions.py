import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("makhmakh")


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        request_id = getattr(
            request.state,
            "request_id",
            str(uuid.uuid4()),
        )

        logger.warning(
            "Request validation error | request_id=%s | method=%s | path=%s",
            request_id,
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid request data",
                    "details": exc.errors(),
                    "request_id": request_id,
                }
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request,
        exc: Exception,
    ):
        request_id = getattr(
            request.state,
            "request_id",
            str(uuid.uuid4()),
        )

        logger.exception(
            "Unhandled exception | request_id=%s | method=%s | path=%s",
            request_id,
            request.method,
            request.url.path,
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An unexpected error occurred",
                    "details": None,
                    "request_id": request_id,
                }
            },
        )