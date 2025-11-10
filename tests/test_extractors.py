"""Tests for pain point extraction logic."""

from __future__ import annotations

import pytest

from src.extractors import pain_point_extractor


def test_deduplicate_pain_points_returns_list() -> None:
    """Ensure deduplication currently returns the input list."""

    mock_points = []
    assert pain_point_extractor.deduplicate_pain_points(mock_points) == mock_points


def test_extract_pain_points_not_implemented() -> None:
    """Placeholder ensuring extraction raises until implemented."""

    with pytest.raises(NotImplementedError):
        pain_point_extractor.extract_pain_points([])
