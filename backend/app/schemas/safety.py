from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.common import Severity, StrictModel

HazardCategory = Literal[
    "ppe",
    "fall",
    "electrical",
    "fire",
    "housekeeping",
    "scaffolding",
    "excavation",
    "lifting",
    "chemical",
    "other",
]
Likelihood = Literal["rare", "unlikely", "possible", "likely", "almost_certain"]
ImageQuality = Literal["good", "fair", "poor", "not_provided"]


class Hazard(StrictModel):
    id: str = Field(min_length=1, max_length=40)
    title: str = Field(min_length=3, max_length=160)
    category: HazardCategory
    severity: Severity
    likelihood: Likelihood
    location: str = Field(min_length=2, max_length=160)
    description: str = Field(min_length=8, max_length=600)
    corrective_action: str = Field(min_length=8, max_length=600)
    ppe_required: list[str] = Field(default_factory=list, max_length=8)


class PpeCompliance(StrictModel):
    overall: Literal["compliant", "partial", "non_compliant", "unknown"]
    observed: list[str] = Field(default_factory=list, max_length=12)
    missing: list[str] = Field(default_factory=list, max_length=12)
    score: int = Field(ge=0, le=100)


class SafetyResult(StrictModel):
    risk_score: int = Field(ge=0, le=100)
    risk_level: Literal["low", "moderate", "high", "critical"]
    summary: str = Field(min_length=20, max_length=1200)
    hazards: list[Hazard] = Field(min_length=1, max_length=20)
    ppe: PpeCompliance
    immediate_actions: list[str] = Field(min_length=1, max_length=10)
    positive_observations: list[str] = Field(default_factory=list, max_length=10)
    confidence: float = Field(ge=0.0, le=1.0)
    image_quality: ImageQuality
    disclaimer: str = Field(min_length=20, max_length=500)
