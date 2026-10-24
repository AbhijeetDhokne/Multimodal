from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import StrictModel

KnowledgeTopic = Literal[
    "concrete",
    "steel",
    "safety",
    "quality",
    "scheduling",
    "costing",
    "procurement",
    "excavation",
    "waterproofing",
    "green_building",
    "contracts",
    "general",
]
ExperienceLevel = Literal["beginner", "intermediate", "expert"]


class KnowledgeRequest(StrictModel):
    question: str = Field(min_length=3, max_length=1500)
    topic: KnowledgeTopic = "general"
    experience_level: ExperienceLevel = "intermediate"

    @field_validator("question")
    @classmethod
    def _clean_question(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 3:
            raise ValueError("Question must contain at least 3 characters.")
        return cleaned


class KnowledgeReference(StrictModel):
    title: str = Field(min_length=3, max_length=180)
    source: str = Field(min_length=2, max_length=180)


class KnowledgeResult(StrictModel):
    topic: KnowledgeTopic
    answer: str = Field(min_length=20, max_length=4000)
    key_points: list[str] = Field(min_length=1, max_length=12)
    practical_tips: list[str] = Field(default_factory=list, max_length=10)
    references: list[KnowledgeReference] = Field(default_factory=list, max_length=8)
    related_topics: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)
    disclaimer: str = Field(min_length=20, max_length=500)
