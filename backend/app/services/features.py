from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from pydantic import Field, ValidationError

from app.schemas.assistant import AssistantRequest, AssistantResult
from app.schemas.crack import CrackResult
from app.schemas.knowledge import KnowledgeRequest, KnowledgeResult
from app.schemas.planning import DesignConcept, PlanningRequest, PlanningResult
from app.schemas.safety import SafetyResult
from app.schemas.common import StrictModel
from app.schemas.valuation import ValuationFactor, ValuationRequest, ValuationResult
from app.services import demo
from app.services.ai import request_json
from app.services.image_utils import ProcessedImage

DEMO_NOTICE = (
    "Demo intelligence engine is active. Add GEMINI_API_KEY (or OPENAI_API_KEY) "
    "to backend/.env for live multimodal analysis."
)


@dataclass
class FeatureOutcome:
    result: Any
    provider: str
    model: str | None
    notices: list[str] = field(default_factory=list)


class PlanningNarrative(StrictModel):
    concept: DesignConcept
    risks: list[str] = Field(min_length=1, max_length=20)
    recommendations: list[str] = Field(min_length=1, max_length=20)
    assumptions: list[str] = Field(min_length=1, max_length=20)


class ValuationNarrative(StrictModel):
    summary: str = Field(min_length=20, max_length=1200)
    valuation_factors: list[ValuationFactor] = Field(min_length=1, max_length=15)
    recommendations: list[str] = Field(min_length=1, max_length=10)
    assumptions: list[str] = Field(min_length=1, max_length=12)


def _demo_fallback(result: Any, notice: str | None = None) -> FeatureOutcome:
    notices = [DEMO_NOTICE]
    if notice:
        notices.append(notice)
    return FeatureOutcome(result=result, provider="fallback", model=None, notices=notices)


def _validation_fallback(result: Any, error: Exception) -> FeatureOutcome:
    return _demo_fallback(
        result,
        f"Live AI output failed strict schema validation; offline engine used instead ({error.__class__.__name__}).",
    )


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------


async def analyze_safety(
    *,
    image: ProcessedImage | None,
    description: str,
    project_type: str,
    location: str,
    activity: str,
    api_key: str | None = None,
    provider: str | None = None,
) -> FeatureOutcome:
    demo_result = demo.demo_safety(
        description=description,
        project_type=project_type,
        location=location,
        activity=activity,
        stats=image.stats if image else None,
    )
    context = json.dumps(
        {
            "project_type": project_type,
            "site_location": location,
            "work_activity": activity,
            "site_notes": description or "(none)",
            "image_supplied": image is not None,
        }
    )
    instruction = (
        "Perform a construction site safety review. Identify 3-8 credible hazards with severity, "
        "likelihood, location, and corrective action. Assess PPE compliance. If the image does not "
        "support a confident visual finding, reduce confidence and state the limitation."
    )
    outcome = await request_json(
        SafetyResult,
        instruction=instruction,
        context=context,
        image=image,
        api_key=api_key,
        provider=provider,
    )
    if outcome.data is None:
        return _demo_fallback(demo_result, outcome.notice)
    try:
        result = SafetyResult.model_validate(outcome.data)
    except ValidationError as exc:
        return _validation_fallback(demo_result, exc)
    return FeatureOutcome(result=result, provider=outcome.provider, model=outcome.model)


# ---------------------------------------------------------------------------
# Crack analysis
# ---------------------------------------------------------------------------


async def analyze_crack(
    *,
    image: ProcessedImage,
    description: str,
    structure_type: str,
    api_key: str | None = None,
    provider: str | None = None,
) -> FeatureOutcome:
    demo_result = demo.demo_crack(
        description=description,
        structure_type=structure_type,
        stats=image.stats,
    )
    context = json.dumps(
        {
            "structure_element": structure_type,
            "inspector_notes": description or "(none)",
        }
    )
    instruction = (
        "Act as a structural inspection assistant. Analyze the construction image for cracks. "
        "Classify crack type, severity, likely causes, measurements, urgency, and whether a "
        "professional inspection is required. Do not overstate certainty from a single photograph."
    )
    outcome = await request_json(
        CrackResult,
        instruction=instruction,
        context=context,
        image=image,
        api_key=api_key,
        provider=provider,
    )
    if outcome.data is None:
        return _demo_fallback(demo_result, outcome.notice)
    try:
        result = CrackResult.model_validate(outcome.data)
    except ValidationError as exc:
        return _validation_fallback(demo_result, exc)
    return FeatureOutcome(result=result, provider=outcome.provider, model=outcome.model)


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------


async def build_plan(
    req: PlanningRequest, api_key: str | None = None, provider: str | None = None
) -> FeatureOutcome:
    baseline = demo.demo_planning(req)
    context = json.dumps(
        {
            "brief": req.model_dump(mode="json"),
            "deterministic_baseline": {
                "total_cost": baseline.cost.total,
                "currency": baseline.currency,
                "cost_per_sqft": baseline.cost.cost_per_sqft,
                "total_duration_days": baseline.schedule.total_duration_days,
                "critical_path": baseline.schedule.critical_path,
                "typical_floor_area_sqft": baseline.floor_plan.typical_floor_area_sqft,
            },
        }
    )
    instruction = (
        "Create the design concept and professional planning narrative for this construction "
        "project. Do NOT change the deterministic cost, material, schedule, or room-layout values; "
        "they are owned by the estimator. Provide an architectural concept, project risks, "
        "recommendations, and estimation assumptions."
    )
    outcome = await request_json(
        PlanningNarrative,
        instruction=instruction,
        context=context,
        image=None,
        api_key=api_key,
        provider=provider,
    )
    if outcome.data is None:
        return _demo_fallback(baseline, outcome.notice)
    try:
        narrative = PlanningNarrative.model_validate(outcome.data)
    except ValidationError as exc:
        return _validation_fallback(baseline, exc)
    merged = baseline.model_copy(
        update={
            "concept": narrative.concept,
            "risks": narrative.risks,
            "recommendations": narrative.recommendations,
            "assumptions": narrative.assumptions,
        }
    )
    return FeatureOutcome(
        result=merged,
        provider=outcome.provider,
        model=outcome.model,
        notices=["Costs, quantities, schedule, and floor layout are computed deterministically; the design narrative is AI-generated."],
    )


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------


async def estimate_valuation(
    req: ValuationRequest, api_key: str | None = None, provider: str | None = None
) -> FeatureOutcome:
    baseline = demo.demo_valuation(req)
    context = json.dumps(
        {
            "property": req.model_dump(mode="json"),
            "deterministic_baseline": {
                "estimated_value": baseline.estimated_value,
                "range": [baseline.value_range_low, baseline.value_range_high],
                "price_per_sqft": baseline.price_per_sqft,
                "market_outlook": baseline.market_outlook,
            },
        }
    )
    instruction = (
        "Write a professional real-estate valuation narrative using the deterministic baseline. "
        "Do NOT change the estimated value, range, price per square foot, or market outlook. "
        "Explain the valuation factors, recommendations, and assumptions. Currency is INR."
    )
    outcome = await request_json(
        ValuationNarrative,
        instruction=instruction,
        context=context,
        image=None,
        api_key=api_key,
        provider=provider,
    )
    if outcome.data is None:
        return _demo_fallback(baseline, outcome.notice)
    try:
        narrative = ValuationNarrative.model_validate(outcome.data)
    except ValidationError as exc:
        return _validation_fallback(baseline, exc)
    merged = baseline.model_copy(
        update={
            "summary": narrative.summary,
            "valuation_factors": narrative.valuation_factors,
            "recommendations": narrative.recommendations,
            "assumptions": narrative.assumptions,
        }
    )
    return FeatureOutcome(result=merged, provider=outcome.provider, model=outcome.model)


# ---------------------------------------------------------------------------
# Knowledge
# ---------------------------------------------------------------------------


async def answer_knowledge(
    req: KnowledgeRequest, api_key: str | None = None, provider: str | None = None
) -> FeatureOutcome:
    demo_result = demo.demo_knowledge(req)
    matches = demo.find_knowledge(req.question, req.topic, limit=2)
    kb_context = [
        {
            "title": entry["title"],
            "summary": entry["summary"],
            "key_points": entry["key_points"],
            "references": entry["references"],
        }
        for entry in matches
    ]
    context = json.dumps(
        {
            "question": req.question,
            "topic": req.topic,
            "experience_level": req.experience_level,
            "knowledge_base_excerpts": kb_context,
        }
    )
    instruction = (
        "Answer the construction knowledge question with accurate, practical guidance. "
        "Use the supplied knowledge-base excerpts when relevant, cite them, and add related topics. "
        "Be clear about code-specific limitations and recommend the latest local standards."
    )
    outcome = await request_json(
        KnowledgeResult,
        instruction=instruction,
        context=context,
        image=None,
        api_key=api_key,
        provider=provider,
    )
    if outcome.data is None:
        return _demo_fallback(demo_result, outcome.notice)
    try:
        result = KnowledgeResult.model_validate(outcome.data)
    except ValidationError as exc:
        return _validation_fallback(demo_result, exc)
    return FeatureOutcome(result=result, provider=outcome.provider, model=outcome.model)


# ---------------------------------------------------------------------------
# Site assistant
# ---------------------------------------------------------------------------


async def answer_assistant(
    req: AssistantRequest, api_key: str | None = None, provider: str | None = None
) -> FeatureOutcome:
    demo_result = demo.demo_assistant(req)
    matches = demo.find_knowledge(req.message, limit=2)
    kb_context = [
        {"title": entry["title"], "summary": entry["summary"], "key_points": entry["key_points"]}
        for entry in matches
    ]
    conversation = [
        {"role": turn.role, "content": turn.content[-1200:]} for turn in req.conversation[-8:]
    ]
    context = json.dumps(
        {
            "project_context": req.project_context.model_dump(mode="json"),
            "question": req.message,
            "conversation": conversation,
            "knowledge_base_excerpts": kb_context,
        }
    )
    instruction = (
        "Act as a daily site assistant for a construction professional. Give a decisive, practical "
        "answer, concrete action items, relevant safety alerts, follow-up questions, and references. "
        "Do not invent approvals or code clauses. Keep the answer concise and field-ready."
    )
    outcome = await request_json(
        AssistantResult,
        instruction=instruction,
        context=context,
        image=None,
        api_key=api_key,
        provider=provider,
    )
    if outcome.data is None:
        return _demo_fallback(demo_result, outcome.notice)
    try:
        result = AssistantResult.model_validate(outcome.data)
    except ValidationError as exc:
        return _validation_fallback(demo_result, exc)
    return FeatureOutcome(result=result, provider=outcome.provider, model=outcome.model)
