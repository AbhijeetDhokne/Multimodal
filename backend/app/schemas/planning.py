from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import StrictModel

ProjectType = Literal["residential", "commercial", "industrial", "infrastructure", "renovation"]
ProjectQuality = Literal["economy", "standard", "premium", "luxury"]
Currency = Literal["INR", "USD"]


class PlanningRequest(StrictModel):
    project_type: ProjectType
    built_up_area_sqft: float = Field(ge=200, le=10_000_000)
    floors: int = Field(ge=1, le=60)
    location: str = Field(min_length=2, max_length=80)
    quality: ProjectQuality = "standard"
    start_date: date
    currency: Currency = "INR"
    notes: str | None = Field(default=None, max_length=1200)

    @field_validator("location")
    @classmethod
    def _clean_location(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("Location must not be empty.")
        return cleaned


class MaterialItem(StrictModel):
    name: str = Field(min_length=2, max_length=80)
    quantity: float = Field(ge=0)
    unit: str = Field(min_length=1, max_length=20)
    unit_cost: float = Field(ge=0)
    estimated_cost: float = Field(ge=0)
    notes: str = Field(default="", max_length=240)


class CostBreakdown(StrictModel):
    structural: float = Field(ge=0)
    finishing: float = Field(ge=0)
    mep: float = Field(ge=0)
    labor: float = Field(ge=0)
    permits: float = Field(ge=0)
    contingency: float = Field(ge=0)
    total: float = Field(ge=0)
    cost_per_sqft: float = Field(ge=0)


class Task(StrictModel):
    id: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=2, max_length=120)
    phase: str = Field(min_length=2, max_length=60)
    duration_days: int = Field(ge=1, le=3650)
    start_day: int = Field(ge=1)
    end_day: int = Field(ge=1)
    start_date: date
    end_date: date
    depends_on: list[str] = Field(default_factory=list)


class Schedule(StrictModel):
    total_duration_days: int = Field(ge=1)
    start_date: date
    end_date: date
    tasks: list[Task] = Field(min_length=1, max_length=60)
    critical_path: list[str] = Field(default_factory=list)


class ColorSwatch(StrictModel):
    name: str = Field(min_length=2, max_length=40)
    hex: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")


class DesignConcept(StrictModel):
    style: str = Field(min_length=2, max_length=100)
    description: str = Field(min_length=30, max_length=900)
    key_features: list[str] = Field(min_length=1, max_length=10)
    color_palette: list[ColorSwatch] = Field(min_length=2, max_length=8)
    sustainability_notes: list[str] = Field(default_factory=list, max_length=10)


class RoomLayout(StrictModel):
    name: str = Field(min_length=2, max_length=60)
    room_type: str = Field(min_length=2, max_length=40)
    x_ft: float = Field(ge=0)
    y_ft: float = Field(ge=0)
    width_ft: float = Field(gt=0)
    length_ft: float = Field(gt=0)
    area_sqft: float = Field(gt=0)


class FloorPlan(StrictModel):
    total_width_ft: float = Field(gt=0)
    total_length_ft: float = Field(gt=0)
    typical_floor_area_sqft: float = Field(gt=0)
    rooms: list[RoomLayout] = Field(min_length=1, max_length=30)
    notes: list[str] = Field(default_factory=list, max_length=8)


class PlanningResult(StrictModel):
    project_type: ProjectType
    built_up_area_sqft: float = Field(gt=0)
    floors: int = Field(ge=1)
    location: str
    quality: ProjectQuality
    currency: Currency
    cost: CostBreakdown
    materials: list[MaterialItem] = Field(min_length=1, max_length=30)
    schedule: Schedule
    concept: DesignConcept
    floor_plan: FloorPlan
    assumptions: list[str] = Field(min_length=1, max_length=20)
    risks: list[str] = Field(min_length=1, max_length=20)
    recommendations: list[str] = Field(min_length=1, max_length=20)
