"""Tests for the Streamlit query input helpers."""

from __future__ import annotations

import pytest

from app.components import query_input


@pytest.mark.parametrize(
    "raw_text, expected",
    [
        (" leading and trailing  ", "leading and trailing"),
        ("multiple    spaces   inside", "multiple spaces inside"),
        ("\nnewlines\tand tabs", "newlines and tabs"),
    ],
)
def test_normalize_query_cleans_whitespace(raw_text: str, expected: str) -> None:
    """normalize_query should trim and collapse whitespace."""

    assert query_input.normalize_query(raw_text) == expected


@pytest.mark.parametrize(
    "clean_text, expected",
    [
        ("", 0),
        ("single", 1),
        ("two words", 2),
        ("three distinct words", 3),
    ],
)
def test_count_words_returns_expected_totals(clean_text: str, expected: int) -> None:
    """count_words returns accurate word totals for the cleaned text."""

    assert query_input.count_words(clean_text) == expected


def test_validate_query_rejects_empty_text() -> None:
    """Queries must include at least one word."""

    is_valid, message = query_input.validate_query("")

    assert not is_valid
    assert "Enter at least one word" in message


def test_validate_query_rejects_queries_longer_than_limit() -> None:
    """Queries over the limit should return a descriptive error."""

    over_limit_query = " ".join([f"word{i}" for i in range(query_input.WORD_MAX + 2)])

    is_valid, message = query_input.validate_query(over_limit_query)

    assert not is_valid
    assert str(query_input.WORD_MAX) in message


def test_validate_query_accepts_query_within_limits() -> None:
    """A well-formed query within limits returns success and no message."""

    valid_query = "investigate why the billing dashboard errors during peak hours"

    is_valid, message = query_input.validate_query(valid_query)

    assert is_valid
    assert message is None

