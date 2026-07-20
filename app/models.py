"""Validated research request, response, and status models."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ResearchStatus(StrEnum):
    DRAFT = "draft"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    FAILED = "failed"


class ResearchRequest(BaseModel):
    question: str = Field(min_length=10, max_length=2000)
    audience: str = Field(default="general", min_length=2, max_length=120)
    approved_to_save: bool = False

    @field_validator("question")
    @classmethod
    def reject_vague_questions(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        vague = {"help me", "research this", "tell me everything"}
        if cleaned.casefold() in vague:
            raise ValueError("Research question is too broad; add a specific objective.")
        return cleaned


class SourceReference(BaseModel):
    file_name: str
    page_label: str | None = None
    score: float | None = None


class ResearchResponse(BaseModel):
    report_id: str
    status: ResearchStatus
    result: str
    sources: list[SourceReference] = Field(default_factory=list)
    confidence: Literal["Low", "Moderate"] = "Low"
    prompt_tokens: int = 0
    completion_tokens: int = 0
    embedding_tokens: int = 0
    estimated_cost_usd: float = 0.0
