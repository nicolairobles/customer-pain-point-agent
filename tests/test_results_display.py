"""Tests for the results display helper functions."""

from __future__ import annotations

from app.components import results_display


def test_build_metadata_summary_formats_values() -> None:
    """Metadata should format numbers into friendly strings."""

    stats = results_display.build_metadata_summary(
        {"total_sources_searched": 7, "execution_time": 1.2345, "api_costs": 0.00456}
    )

    assert [stat.label for stat in stats] == ["Sources Searched", "Execution Time", "API Cost"]
    assert stats[0].value == "7"
    assert stats[1].value == "1.23s"
    assert stats[2].value == "$0.005"


def test_build_metadata_summary_handles_missing_fields() -> None:
    """Missing metadata should fall back to zeroed values."""

    stats = results_display.build_metadata_summary({})
    assert [stat.value for stat in stats] == ["0", "0.00s", "$0.000"]


def test_normalize_pain_points_populates_defaults() -> None:
    """Pain point normalization fills in sensible defaults and trims text."""

    normalized = results_display.normalize_pain_points(
        [
            {
                "name": "Slow Reports",
                "description": "The reporting dashboard is slow when exporting data." * 10,
                "frequency": 12,
                "examples": ["Export takes >5 minutes", "Timeout errors in Safari"],
                "sources": [
                    {"platform": "Reddit", "url": "https://reddit.com/example"},
                    {"title": "Support Ticket #42"},
                ],
            },
            {
                # intentionally minimal payload to exercise defaults
            },
        ]
    )

    assert normalized[0].title == "Slow Reports"
    assert normalized[0].frequency_label == "Frequency: 12"
    assert len(normalized[0].summary) <= 280
    assert normalized[0].examples == ["Export takes >5 minutes", "Timeout errors in Safari"]
    assert normalized[0].citations == ["[Reddit](https://reddit.com/example)", "Support Ticket #42"]

    assert normalized[1].title == "Pain Point 2"
    assert normalized[1].summary.startswith("No description provided")
    assert normalized[1].frequency_label == "Frequency: not provided"
    assert normalized[1].examples == []
    assert normalized[1].citations == []


def test_coerce_message_list_collapses_values() -> None:
    """Coerce message helper should return a deduplicated list of strings."""

    assert results_display._coerce_message_list(None) == []
    assert results_display._coerce_message_list("A single issue") == ["A single issue"]
    assert results_display._coerce_message_list(["err1", "", "err2"]) == ["err1", "err2"]
    assert results_display._coerce_message_list({"detail": "boom"}) == ["{'detail': 'boom'}"]

