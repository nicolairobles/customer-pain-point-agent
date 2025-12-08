"""Formatting utilities for presentation and logging."""

from __future__ import annotations

import math
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


def _coerce_finite_float(value: Optional[float]) -> Optional[float]:
    """Attempt to coerce a value to a finite float, returning None otherwise."""

    try:
        coerced = float(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None

    if math.isnan(coerced) or math.isinf(coerced):
        return None

    return coerced


def format_duration(seconds: Optional[float]) -> str:
    """Convert a raw duration to a user-friendly string."""

    coerced = _coerce_finite_float(seconds)
    if coerced is None:
        return "0.00s"
    return f"{coerced:.2f}s"


def format_currency(amount: Optional[float]) -> str:
    """Format API cost figures in USD with mill precision."""

    coerced = _coerce_finite_float(amount)
    if coerced is None:
        return "$0.000"
    return f"${coerced:,.3f}"
