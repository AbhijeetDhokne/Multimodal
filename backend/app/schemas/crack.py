from __future__ import annotations

from typing import Literal

from pydantic import Field

from app.schemas.common import StrictModel
from app.schemas.safety import ImageQuality

CrackType = Literal[
    "hairline",
    "structural",
    "settlement",
    "shrinkage",
    "thermal",
    "shear",
    "flexural",
    "corrosion",
    "unknown",
]
CrackSeverity = Literal["minor", "moderate", "severe", "critical"]
Urgency = Literal["monitor", "schedule_repair", "urgent", "emergency"]


class CrackMeasurement(StrictModel):
    estimated_length_cm: float | None = Field(default=None, ge=0, le=10000)
    estimated_width_mm: float | None = Field(default=None, ge=0, le=500)
    confidence: float = Field(ge=0.0, le=1.0)


class CrackResult(StrictModel):
    detected: bool
    crack_type: CrackType
    severity: CrackSeverity
    severity_score: int = Field(ge=0, le=100)
    summary: str = Field(min_length=20, max_length=1200)
    affected_element: str = Field(min_length=2, max_length=160)
    probable_causes: list[str] = Field(min_length=1, max_length=10)
    measurements: CrackMeasurement
    recommended_actions: list[str] = Field(min_length=1, max_length=10)
    urgency: Urgency
    requires_professional_inspection: bool
    confidence: float = Field(ge=0.0, le=1.0)
    image_quality: ImageQuality
    disclaimer: str = Field(min_length=20, max_length=500)
