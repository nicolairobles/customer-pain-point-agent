"""Prompt templates used by the pain point extraction pipeline."""

from .pain_point_prompt import (
    PAIN_POINT_PROMPT_VERSION,
    PainPointPrompt,
    format_documents_for_prompt,
)

__all__ = [
    "PainPointPrompt",
    "PAIN_POINT_PROMPT_VERSION",
    "format_documents_for_prompt",
]

