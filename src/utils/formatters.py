"""Formatting utilities for presentation and logging."""

from __future__ import annotations

from typing import Any, Dict, List


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
