from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import error_response, router
from app.config import settings
from app.context import current_request_id, request_id_ctx

logging.basicConfig(
    level=logging.INFO if not settings.debug else logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger("constructiq")

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Multimodal construction intelligence API for safety, crack analysis, planning, "
        "valuation, site assistance, weather and knowledge support. All feature responses "
        "follow strict JSON contracts."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    token = request_id_ctx.set(request_id)
    try:
        content_length = request.headers.get("content-length")
        if content_length and content_length.isdigit():
            if int(content_length) > settings.max_upload_bytes + 2 * 1024 * 1024:
                return error_response(
                    413,
                    "payload_too_large",
                    f"Request payload exceeds the {settings.max_upload_mb} MB upload limit.",
                )
        response = await call_next(request)
    finally:
        request_id_ctx.reset(token)
    response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    details = []
    for error in exc.errors():
        location = [
            str(part)
            for part in error.get("loc", [])
            if part not in {"body", "query", "form", "path"}
        ]
        details.append(
            {
                "field": ".".join(location) if location else None,
                "message": str(error.get("msg", "Invalid value")),
            }
        )
    return error_response(422, "validation_error", "Request validation failed.", details)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    message = exc.detail if isinstance(exc.detail, str) else "The request could not be completed."
    if exc.status_code == 404:
        message = "The requested endpoint does not exist."
    return error_response(exc.status_code, "not_found" if exc.status_code == 404 else "http_error", message)


from app.errors import AppError  # noqa: E402


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return error_response(exc.status_code, exc.code, exc.message, exc.details)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s [request_id=%s]", request.method, request.url.path, current_request_id())
    return error_response(500, "internal_error", "An unexpected server error occurred.")


app.include_router(router)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
        "docs": "/docs",
        "health": "/api/health",
        "features": [
            "safety",
            "crack",
            "planning",
            "valuation",
            "assistant",
            "weather",
            "knowledge",
        ],
    }
