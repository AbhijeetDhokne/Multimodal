from __future__ import annotations

from typing import Any


class AppError(Exception):
    """Application-level error that maps to the public JSON error envelope."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int = 400,
        code: str = "bad_request",
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.code = code
        self.details = details or []


class ImageValidationError(AppError):
    def __init__(self, message: str, *, status_code: int = 415) -> None:
        super().__init__(message, status_code=status_code, code="invalid_image")
