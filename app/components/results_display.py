"""Streamlit component for rendering agent results."""

from __future__ import annotations

from typing import Any, Dict, List

import streamlit as st

from src.utils.formatters import format_source_list, truncate_description


def render_results(results: Dict[str, Any]) -> None:
    """Display agent results in a structured layout."""

    pain_points: List[Dict[str, Any]] = results.get("pain_points", [])
    metadata = results.get("metadata", {})

    if not pain_points:
        st.info("No pain points identified yet. Try refining your query.")
        return

    st.subheader("Insights")
    for pain_point in pain_points:
        with st.expander(pain_point.get("name", "Unknown Pain Point"), expanded=True):
            st.write(truncate_description(pain_point.get("description", "")))
            st.write(f"Frequency: {pain_point.get('frequency', 'unknown')}")
            examples = pain_point.get("examples", [])
            if examples:
                st.write("Examples:")
                for example in examples:
                    st.markdown(f"- {example}")
            st.caption(format_source_list(pain_point.get("sources", [])))

    st.subheader("Metadata")
    st.json(metadata)
