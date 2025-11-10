"""Validation helpers for incoming queries and configuration values."""

from __future__ import annotations

from typing import Iterable


class ValidationError(Exception):
    """Raised when input data fails validation rules."""


def validate_query_length(query: str, min_words: int = 1, max_words: int = 50) -> None:
    """Ensure the query word count is within the accepted range."""

    word_count = len(query.split())
    if word_count < min_words or word_count > max_words:
        raise ValidationError(
            f"Query must contain between {min_words} and {max_words} words; received {word_count}."
        )


def ensure_non_empty(values: Iterable[str]) -> None:
    """Ensure an iterable of strings does not contain empty entries."""

    for value in values:
        if not value:
            raise ValidationError("Encountered empty value where non-empty string was expected.")
