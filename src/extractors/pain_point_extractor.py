"""Pain point extraction routines powered by OpenAI."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field

from config.settings import settings


class PainPointSource(BaseModel):
    """Metadata describing where a pain point observation originated."""

    platform: str
    url: str
    timestamp: str
    author: str


class PainPoint(BaseModel):
    """Structured representation of a customer pain point."""

    name: str
    description: str
    frequency: str = Field(regex=r"^(high|medium|low)$")
    examples: List[str]
    sources: List[PainPointSource]


def extract_pain_points(raw_documents: List[Dict[str, Any]]) -> List[PainPoint]:
    """Transform raw tool outputs into structured pain points."""

    # TODO: Implement OpenAI call and parsing logic
    raise NotImplementedError("extract_pain_points needs implementation")


def deduplicate_pain_points(pain_points: List[PainPoint]) -> List[PainPoint]:
    """Remove duplicate pain points while preserving metadata."""

    # TODO: Implement deduplication logic
    return pain_points
