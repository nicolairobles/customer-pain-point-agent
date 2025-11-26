"""Streamlit component for rendering agent results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Sequence

import streamlit as st

from src.utils.formatters import format_currency, format_duration, truncate_description

_STYLE_SESSION_KEY = "results_component_styles_loaded"
_RESULTS_STYLE = """
<style>
.pp-results-metrics {
    background: rgba(239, 234, 242, 0.85);
    border-radius: 16px;
    padding: 18px;
    color: #2d1b3d;
}
.pp-results-metrics h4 {
    margin: 0;
    font-size: 0.95rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #7a708b;
}
.pp-results-metrics p {
    margin: 6px 0 0;
    font-size: 1.35rem;
    font-weight: 700;
    color: #2d1b3d;
}
.pp-card {
    background: rgba(239, 234, 242, 0.92);
    border-radius: 18px;
    padding: 20px 24px;
    color: #2d1b3d;
    box-shadow: 0 12px 24px rgba(27, 14, 33, 0.08);
    margin-bottom: 12px;
}
.pp-card p {
    margin: 0 0 12px;
    line-height: 1.5;
}
.pp-card .pp-frequency {
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    font-size: 0.85rem;
    color: #7a708b;
}
.pp-card ul {
    margin: 0 0 8px 18px;
}
.pp-card li {
    margin-bottom: 4px;
}
.pp-citations {
    font-size: 0.9rem;
    color: #4b3b61;
}
</style>
"""


@dataclass
class MetadataStat:
    label: str
    value: str
    help_text: str | None = None


@dataclass
class PainPointDisplay:
    title: str
    summary: str
    frequency_label: str
    examples: List[str]
    citations: List[str]


def _inject_styles() -> None:
    """Ensure component-specific styling is applied once per session."""

    if st.session_state.get(_STYLE_SESSION_KEY):
        return
    st.markdown(_RESULTS_STYLE, unsafe_allow_html=True)
    st.session_state[_STYLE_SESSION_KEY] = True


def build_metadata_summary(metadata: Dict[str, Any]) -> List[MetadataStat]:
    """Create user-friendly metadata rows for display."""

    total_sources = metadata.get("total_sources_searched") or metadata.get("total_sources") or 0
    executions = metadata.get("execution_time") or metadata.get("execution_time_seconds") or 0.0
    cost = metadata.get("api_costs") or metadata.get("cost_usd") or 0.0

    return [
        MetadataStat("Sources Searched", f"{int(total_sources)}"),
        MetadataStat("Execution Time", format_duration(executions)),
        MetadataStat("API Cost", format_currency(cost)),
    ]


def normalize_pain_points(pain_points: Iterable[Dict[str, Any]]) -> List[PainPointDisplay]:
    """Coerce raw pain point payloads into display-friendly structures."""

    normalized: List[PainPointDisplay] = []

    for idx, raw in enumerate(pain_points):
        title = raw.get("name") or f"Pain Point {idx + 1}"
        description = raw.get("description") or "No description provided."
        frequency = raw.get("frequency")

        if frequency in (None, "", 0):
            frequency_label = "Frequency: not provided"
        elif isinstance(frequency, (int, float)):
            frequency_label = f"Frequency: {frequency}"
        else:
            frequency_label = f"Frequency: {frequency}"

        examples = [example.strip() for example in raw.get("examples", []) if str(example).strip()]

        citations: List[str] = []
        for source in raw.get("sources", []):
            title_or_platform = source.get("title") or source.get("platform") or "Source"
            url = source.get("url")
            if url:
                citations.append(f"[{title_or_platform}]({url})")
            else:
                citations.append(title_or_platform)

        normalized.append(
            PainPointDisplay(
                title=title,
                summary=truncate_description(description, max_length=280),
                frequency_label=frequency_label,
                examples=examples,
                citations=citations,
            )
        )

    return normalized


def _coerce_message_list(value: Any) -> List[str]:
    """Convert error/warning payloads into a flat list of messages."""

    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)]


def render_results(results: Dict[str, Any]) -> None:
    """Display agent results in a structured layout."""

    _inject_styles()

    pain_points = normalize_pain_points(results.get("pain_points", []))
    metadata = build_metadata_summary(results.get("metadata", {}))
    errors = _coerce_message_list(results.get("errors"))
    warnings = _coerce_message_list(
        results.get("warnings")
        or results.get("partial_failures")
        or results.get("diagnostics", {}).get("warnings")  # diagnostics is optional
    )

    if errors:
        st.error("We ran into issues while aggregating results:")
        for message in errors:
            st.markdown(f"- {message}")

    if warnings:
        st.warning("Partial results returned; some sources may be missing:")
        for message in warnings:
            st.markdown(f"- {message}")

    if not pain_points:
        st.info("No pain points identified yet. Try refining your query or adjusting filters.")
        return

    st.subheader("Summary")
    metric_columns = st.columns(len(metadata))
    for column, stat in zip(metric_columns, metadata):
        with column:
            column.markdown(
                f"<div class='pp-results-metrics'><h4>{stat.label}</h4><p>{stat.value}</p></div>",
                unsafe_allow_html=True,
            )
            if stat.help_text:
                column.caption(stat.help_text)

    st.subheader("Insights")
    tab_labels = [display.title for display in pain_points]
    tabs = st.tabs(tab_labels)

    for tab, pain_point in zip(tabs, pain_points):
        with tab:
            st.markdown(
                f"""
                <div class="pp-card">
                    <p>{pain_point.summary}</p>
                    <p class="pp-frequency">{pain_point.frequency_label}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if pain_point.examples:
                st.markdown("**Examples**")
                for example in pain_point.examples:
                    st.markdown(f"- {example}")

            if pain_point.citations:
                st.markdown("**Source Citations**")
                for citation in pain_point.citations:
                    st.markdown(f"- {citation}", unsafe_allow_html=True)

