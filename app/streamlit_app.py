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

from src.utils.validators import ValidationError, validate_query_length
from app.components.query_input import render_query_input
from app.components.results_display import render_results
try:
    from src.agent.pain_point_agent import run_agent
except ImportError:  # pragma: no cover - executed in environments without agent deps
    run_agent = None  # type: ignore[assignment]

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

        if run_agent is None:
            st.warning(
                "The LangChain agent dependencies are not available in this environment. "
                "See the 1.3.x stories for installation/pinning guidance."
            )
            return

        try:
            with st.spinner("Gathering insights from Reddit, Twitter, and Google..."):
                results = run_agent(query)
        except ImportError as exc:
            st.error(
                "Unable to initialize the LangChain agent. Confirm the `langchain` package "
                "matches the project's supported version or complete the agent wiring stories. "
                f"Details: {exc}"
            )
            return

        render_results(results)


if __name__ == "__main__":
    main()
