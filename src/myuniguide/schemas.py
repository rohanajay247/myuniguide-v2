"""The contract between the LLM and the rest of the system.

The LLM is not allowed to return free-form text. It returns this, or the call fails.

Kept deliberately flat: Gemini's response_schema does not support every Pydantic
feature. No Optional fields, no unions, no default_factory — every field is
required and lists come back empty rather than absent.
"""

from enum import Enum

from pydantic import BaseModel, Field


class Decision(str, Enum):
    ANSWER = "ANSWER"
    DECLINE = "DECLINE"
    CONFLICT = "CONFLICT"


class Citation(BaseModel):
    document: str = Field(description="Source document filename")
    locus: str = Field(description="Section reference, e.g. '§ 12 Abs. 3' or 'Artikel 2'")
    quote: str = Field(description="The sentence from the source that supports the claim")


class ConflictDetail(BaseModel):
    summary: str = Field(description="What the two provisions disagree about")
    citations: list[Citation] = Field(description="One citation per conflicting provision")


class AnswerResponse(BaseModel):
    decision: Decision
    answer: str = Field(description="The answer, or the reason for declining")
    citations: list[Citation] = Field(description="Empty unless decision is ANSWER")
    conflicts: list[ConflictDetail] = Field(description="Empty unless decision is CONFLICT")
