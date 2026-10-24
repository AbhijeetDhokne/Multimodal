from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import StrictModel

PropertyType = Literal["apartment", "villa", "plot", "commercial", "office", "retail"]
PropertyQuality = Literal["basic", "standard", "premium", "luxury"]
Condition = Literal["poor", "fair", "good", "excellent"]
Amenity = Literal[
    "parking",
    "gym",
    "pool",
    "security",
    "power_backup",
    "lift",
    "garden",
    "clubhouse",
]


class ValuationRequest(StrictModel):
    property_type: PropertyType
    city: str = Field(min_length=2, max_length=80)
    locality: str | None = Field(default=None, max_length=120)
    area_sqft: float = Field(ge=100, le=1_000_000)
    age_years: int = Field(ge=0, le=100)
    bedrooms: int = Field(ge=0, le=20)
    quality: PropertyQuality = "standard"
    condition: Condition = "good"
    amenities: list[Amenity] = Field(default_factory=list, max_length=8)
    currency: Literal["INR"] = "INR"

    @field_validator("city")
    @classmethod
    def _clean_city(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("City must not be empty.")
        return cleaned

    @field_validator("locality")
    @classmethod
    def _clean_locality(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = " ".join(value.split())
        return cleaned or None


class Comparable(StrictModel):
    description: str = Field(min_length=5, max_length=220)
    area_sqft: float = Field(gt=0)
    price_per_sqft: float = Field(gt=0)
    estimated_value: float = Field(gt=0)


class ValuationFactor(StrictModel):
    factor: str = Field(min_length=2, max_length=80)
    impact: Literal["positive", "neutral", "negative"]
    description: str = Field(min_length=5, max_length=300)


class ValuationResult(StrictModel):
    property_type: PropertyType
    city: str
    locality: str | None
    area_sqft: float = Field(gt=0)
    currency: Literal["INR"]
    estimated_value: int = Field(gt=0)
    value_range_low: int = Field(gt=0)
    value_range_high: int = Field(gt=0)
    price_per_sqft: int = Field(gt=0)
    confidence: float = Field(ge=0.0, le=1.0)
    market_outlook: Literal["declining", "stable", "growing"]
    summary: str = Field(min_length=20, max_length=1200)
    comparable_sales: list[Comparable] = Field(min_length=1, max_length=8)
    valuation_factors: list[ValuationFactor] = Field(min_length=1, max_length=15)
    recommendations: list[str] = Field(min_length=1, max_length=10)
    assumptions: list[str] = Field(min_length=1, max_length=12)
    disclaimer: str = Field(min_length=20, max_length=500)
