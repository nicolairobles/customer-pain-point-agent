"""Formatting utilities for presentation and logging."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def format_source_list(sources: List[Dict[str, Any]]) -> str:
    """Convert a list of sources into a human-readable summary string."""

    formatted = []
    for source in sources:
        platform = source.get("platform", "unknown")
        url = source.get("url", "")
        formatted.append(f"{platform}: {url}")
    return " | ".join(formatted)


def truncate_description(description: str, max_length: int = 200) -> str:
    """Shorten long descriptions for UI display while preserving context."""

    if len(description) <= max_length:
        return description
    return f"{description[: max_length - 3]}..."


def format_duration(seconds: Optional[float]) -> str:
    """Convert a raw duration to a user-friendly string."""

    if seconds is None:
        return "0.00s"
    try:
        return f"{float(seconds):.2f}s"
    except (TypeError, ValueError):
        return "0.00s"


def format_currency(amount: Optional[float]) -> str:
    """Format API cost figures in USD with mill precision."""

    if amount is None:
        return "$0.000"
    try:
        value = float(amount)
    except (TypeError, ValueError):
        return "$0.000"
    return f"${value:,.3f}"
