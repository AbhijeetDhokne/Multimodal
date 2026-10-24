from __future__ import annotations

from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.schemas.common import ApiMeta

request_id_ctx: ContextVar[str] = ContextVar("request_id", default="unknown")


def current_request_id() -> str:
    return request_id_ctx.get()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def build_meta(
    *,
    feature: str,
    provider: str,
    latency_ms: int,
    model: str | None = None,
    notices: list[str] | None = None,
) -> ApiMeta:
    demo_mode = provider in {"demo", "fallback"}
    return ApiMeta(
        request_id=current_request_id(),
        feature=feature,
        provider=provider,  # type: ignore[arg-type]
        model=model,
        generated_at=utc_now(),
        latency_ms=max(0, latency_ms),
        demo_mode=demo_mode,
        notices=notices or [],
        app_version=settings.app_version,
    )


def jsonable(value: Any) -> Any:
    """Best-effort JSON friendly conversion used for logging."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value
