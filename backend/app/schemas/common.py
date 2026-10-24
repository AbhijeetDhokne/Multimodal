from __future__ import annotations

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

AIProvider = Literal["gemini", "openai", "demo", "fallback", "open-meteo"]
FeatureName = Literal[
    "safety",
    "crack",
    "planning",
    "valuation",
    "assistant",
    "weather",
    "knowledge",
    "system",
]
Severity = Literal["low", "medium", "high", "critical"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ApiMeta(StrictModel):
    request_id: str
    feature: FeatureName
    provider: AIProvider
    model: str | None = None
    generated_at: datetime
    latency_ms: int = Field(ge=0)
    demo_mode: bool
    notices: list[str] = Field(default_factory=list)
    app_version: str


T = TypeVar("T", bound=BaseModel)


class ApiResponse(BaseModel, Generic[T]):
    meta: ApiMeta
    result: T


class ErrorDetail(StrictModel):
    field: str | None = None
    message: str


class ErrorBody(StrictModel):
    code: str
    message: str
    request_id: str
    details: list[ErrorDetail] = Field(default_factory=list)


class ErrorResponse(StrictModel):
    error: ErrorBody


class HealthResult(StrictModel):
    status: Literal["ok", "degraded"]
    app_name: str
    version: str
    environment: str
    ai_provider: AIProvider
    ai_model: str | None
    demo_mode: bool
    ai_configured: bool
    features: list[str]
    uptime_seconds: int
    server_time: datetime
    docs_url: str


class HealthResponse(StrictModel):
    meta: ApiMeta
    result: HealthResult
