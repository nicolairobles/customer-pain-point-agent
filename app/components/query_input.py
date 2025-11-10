"""Streamlit component for rendering the query input field."""

from __future__ import annotations

import streamlit as st


def render_query_input() -> str:
    """Render and return the user's query input."""

    return st.text_area(
        label="Describe the customer pain points you want to explore",
        height=150,
        placeholder="Example: Issues customers face when integrating with our API",
    ).strip()
