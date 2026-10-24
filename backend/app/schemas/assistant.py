from __future__ import annotations

from typing import Literal

from pydantic import Field, field_validator

from app.schemas.common import StrictModel


class ChatTurn(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=8000)


class ProjectContext(StrictModel):
    project_type: Literal["residential", "commercial", "industrial", "infrastructure", "renovation"] = (
        "residential"
    )
    stage: Literal[
        "planning",
        "procurement",
        "foundation",
        "structure",
        "finishing",
        "handover",
        "maintenance",
    ] = "planning"
    location: str | None = Field(default=None, max_length=80)
    notes: str | None = Field(default=None, max_length=1200)


class AssistantRequest(StrictModel):
    message: str = Field(min_length=2, max_length=4000)
    project_context: ProjectContext = Field(default_factory=ProjectContext)
    conversation: list[ChatTurn] = Field(default_factory=list, max_length=16)

    @field_validator("message")
    @classmethod
    def _clean_message(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Message must contain at least 2 characters.")
        return cleaned


class AssistantResult(StrictModel):
    answer: str = Field(min_length=20, max_length=4000)
    action_items: list[str] = Field(default_factory=list, max_length=12)
    safety_alerts: list[str] = Field(default_factory=list, max_length=8)
    follow_up_questions: list[str] = Field(default_factory=list, max_length=6)
    references: list[str] = Field(default_factory=list, max_length=8)
    confidence: float = Field(ge=0.0, le=1.0)
    disclaimer: str = Field(min_length=20, max_length=500)
