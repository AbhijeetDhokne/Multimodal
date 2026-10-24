from __future__ import annotations

import time
from typing import Literal

from fastapi import APIRouter, File, Form, Request, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.context import build_meta, utc_now
from app.errors import AppError
from app.schemas.assistant import AssistantRequest, AssistantResult
from app.schemas.common import ApiResponse, HealthResult
from app.schemas.crack import CrackResult
from app.schemas.knowledge import KnowledgeRequest, KnowledgeResult
from app.schemas.planning import PlanningRequest, PlanningResult
from app.schemas.safety import SafetyResult
from app.schemas.valuation import ValuationRequest, ValuationResult
from app.schemas.weather import WeatherResult
from app.services import features
from app.services.image_utils import process_upload
from app.services.weather import get_weather

router = APIRouter(prefix="/api")
STARTED_AT = time.monotonic()


def _elapsed_ms(start: float) -> int:
    return int((time.perf_counter() - start) * 1000)


def _envelope(feature: str, outcome: features.FeatureOutcome, start: float) -> dict:
    meta = build_meta(
        feature=feature,
        provider=outcome.provider,
        latency_ms=_elapsed_ms(start),
        model=outcome.model,
        notices=outcome.notices,
    )
    return {"meta": meta, "result": outcome.result}


@router.get("/health", response_model=ApiResponse[HealthResult], tags=["System"])
async def health() -> dict:
    start = time.perf_counter()
    provider = settings.resolved_provider
    result = HealthResult(
        status="ok",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        ai_provider=provider,  # type: ignore[arg-type]
        ai_model=settings.resolved_model,
        demo_mode=provider == "demo",
        ai_configured=provider != "demo",
        features=[
            "Site Safety Monitor",
            "Crack Analysis",
            "Project Planner",
            "Real Estate Valuation",
            "Site Assistant",
            "Weather Advisory",
            "Knowledge Assistant",
        ],
        uptime_seconds=int(time.monotonic() - STARTED_AT),
        server_time=utc_now(),
        docs_url="/docs",
    )
    meta = build_meta(
        feature="system",
        provider=provider,
        latency_ms=_elapsed_ms(start),
        model=settings.resolved_model,
        notices=[] if provider != "demo" else [features.DEMO_NOTICE],
    )
    return {"meta": meta, "result": result}


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------


@router.post(
    "/safety/analyze",
    response_model=ApiResponse[SafetyResult],
    tags=["Safety"],
    summary="Analyze a construction site image and notes for hazards",
)
async def safety_analyze(
    request: Request,
    image: UploadFile | None = File(default=None),
    description: str = Form(default=""),
    project_type: Literal["residential", "commercial", "industrial", "infrastructure", "renovation"] = Form(
        default="residential"
    ),
    location: str = Form(default="Project site"),
    work_activity: str = Form(default="General construction"),
) -> dict:
    start = time.perf_counter()
    description = (description or "").strip()
    location = (location or "").strip() or "Project site"
    work_activity = (work_activity or "").strip() or "General construction"
    if len(description) > 1500:
        raise AppError("Description must be 1500 characters or fewer.", status_code=422)
    if len(location) > 100 or len(work_activity) > 100:
        raise AppError("Location and work activity must be 100 characters or fewer.", status_code=422)
    if image is None and not description:
        raise AppError(
            "Provide a site image and/or a description so the AI has evidence to analyze.",
            status_code=422,
        )
    processed = await process_upload(image) if image is not None else None
    api_key = request.headers.get("x-ai-api-key") or None
    ai_provider = request.headers.get("x-ai-provider") or None
    outcome = await features.analyze_safety(
        image=processed,
        description=description,
        project_type=project_type,
        location=location,
        activity=work_activity,
        api_key=api_key,
        provider=ai_provider,
    )
    return _envelope("safety", outcome, start)


# ---------------------------------------------------------------------------
# Crack
# ---------------------------------------------------------------------------


@router.post(
    "/crack/analyze",
    response_model=ApiResponse[CrackResult],
    tags=["Crack"],
    summary="Detect and assess cracks from a construction image",
)
async def crack_analyze(
    request: Request,
    image: UploadFile = File(...),
    description: str = Form(default=""),
    structure_type: Literal["auto", "wall", "beam", "column", "slab", "foundation", "ceiling", "plaster"] = Form(
        default="auto"
    ),
) -> dict:
    start = time.perf_counter()
    description = (description or "").strip()
    if len(description) > 1200:
        raise AppError("Description must be 1200 characters or fewer.", status_code=422)
    processed = await process_upload(image)
    api_key = request.headers.get("x-ai-api-key") or None
    ai_provider = request.headers.get("x-ai-provider") or None
    outcome = await features.analyze_crack(
        image=processed,
        description=description,
        structure_type=structure_type,
        api_key=api_key,
        provider=ai_provider,
    )
    return _envelope("crack", outcome, start)


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


@router.post(
    "/planning/plan",
    response_model=ApiResponse[PlanningResult],
    tags=["Planning"],
    summary="Generate cost, materials, schedule, concept and floor plan",
)
async def planning_plan(request: Request, payload: PlanningRequest) -> dict:
    start = time.perf_counter()
    api_key = request.headers.get("x-ai-api-key") or None
    ai_provider = request.headers.get("x-ai-provider") or None
    outcome = await features.build_plan(payload, api_key=api_key, provider=ai_provider)
    return _envelope("planning", outcome, start)


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------


@router.post(
    "/valuation/estimate",
    response_model=ApiResponse[ValuationResult],
    tags=["Valuation"],
    summary="Estimate real-estate value from structured property data",
)
async def valuation_estimate(request: Request, payload: ValuationRequest) -> dict:
    start = time.perf_counter()
    api_key = request.headers.get("x-ai-api-key") or None
    ai_provider = request.headers.get("x-ai-provider") or None
    outcome = await features.estimate_valuation(payload, api_key=api_key, provider=ai_provider)
    return _envelope("valuation", outcome, start)


# ---------------------------------------------------------------------------
# Assistant
# ---------------------------------------------------------------------------


@router.post(
    "/assistant/chat",
    response_model=ApiResponse[AssistantResult],
    tags=["Assistant"],
    summary="Ask the daily site assistant",
)
async def assistant_chat(request: Request, payload: AssistantRequest) -> dict:
    start = time.perf_counter()
    api_key = request.headers.get("x-ai-api-key") or None
    ai_provider = request.headers.get("x-ai-provider") or None
    outcome = await features.answer_assistant(payload, api_key=api_key, provider=ai_provider)
    return _envelope("assistant", outcome, start)


# ---------------------------------------------------------------------------
# Knowledge
# ---------------------------------------------------------------------------


@router.post(
    "/knowledge/ask",
    response_model=ApiResponse[KnowledgeResult],
    tags=["Knowledge"],
    summary="Ask a construction knowledge question",
)
async def knowledge_ask(request: Request, payload: KnowledgeRequest) -> dict:
    start = time.perf_counter()
    api_key = request.headers.get("x-ai-api-key") or None
    ai_provider = request.headers.get("x-ai-provider") or None
    outcome = await features.answer_knowledge(payload, api_key=api_key, provider=ai_provider)
    return _envelope("knowledge", outcome, start)


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------


@router.get(
    "/weather/advisory",
    response_model=ApiResponse[WeatherResult],
    tags=["Weather"],
    summary="Get weather-aware construction advisories",
)
async def weather_advisory(
    city: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> dict:
    start = time.perf_counter()
    if city is not None:
        city = city.strip()
        if len(city) < 2 or len(city) > 80:
            raise AppError("City must be between 2 and 80 characters.", status_code=422)
    if (lat is None) != (lon is None):
        raise AppError("Provide both latitude and longitude, or neither.", status_code=422)
    if lat is not None and not (-90 <= lat <= 90):
        raise AppError("Latitude must be between -90 and 90.", status_code=422)
    if lon is not None and not (-180 <= lon <= 180):
        raise AppError("Longitude must be between -180 and 180.", status_code=422)
    if not city and lat is None:
        raise AppError("Provide a city or latitude/longitude.", status_code=422)

    result, provider, notices = await get_weather(city=city, latitude=lat, longitude=lon)
    meta = build_meta(
        feature="weather",
        provider=provider,
        latency_ms=_elapsed_ms(start),
        model="open-meteo" if provider == "open-meteo" else None,
        notices=notices,
    )
    return {"meta": meta, "result": result}


def error_response(status_code: int, code: str, message: str, details: list[dict] | None = None) -> JSONResponse:
    from app.context import current_request_id

    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": current_request_id(),
                "details": details or [],
            }
        },
    )
