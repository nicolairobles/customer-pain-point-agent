"""Streamlit entry point for the Customer Pain Point Discovery Agent."""

from __future__ import annotations

import streamlit as st

# Ensure repo root is on sys.path so `from src...` imports work when
# running via `streamlit run` (Streamlit changes the CWD/import path).
import sys
import pathlib
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.agent.pain_point_agent import run_agent
from src.utils.validators import ValidationError, validate_query_length
from app.components.query_input import render_query_input
from app.components.results_display import render_results

st.set_page_config(page_title="Customer Pain Point Discovery", layout="wide")


def main() -> None:
    """Render the Streamlit application."""

    st.title("Customer Pain Point Discovery Agent")
    query = render_query_input()

    if st.button("Analyze"):
        try:
            validate_query_length(query)
        except ValidationError as exc:
            st.error(str(exc))
            return

        with st.spinner("Gathering insights from Reddit, Twitter, and Google..."):
            results = run_agent(query)
        render_results(results)


if __name__ == "__main__":
    main()
