"""Streamlit entry point for the Customer Pain Point Discovery Agent."""

from __future__ import annotations

import logging
import os
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
from app.theme import apply_global_styles
try:
    from src.agent.pain_point_agent import run_agent
except ImportError:  # pragma: no cover - executed in environments without agent deps
    run_agent = None  # type: ignore[assignment]

# Configure logging to show in terminal
_log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, _log_level, logging.INFO),
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

st.set_page_config(page_title="Customer Pain Point Discovery", layout="wide")


def main() -> None:
    """Render the Streamlit application."""

    apply_global_styles()
    st.title("Customer Pain Point Discovery Agent")
    query = render_query_input()
    show_debug_panel = os.getenv("SHOW_DEBUG_PANEL", "").strip().lower() in {"1", "true", "yes", "on"}

    if st.button("Analyze"):
        try:
            validate_query_length(query)
        except ValidationError as exc:
            st.error(str(exc))
            return

        if run_agent is None:
            st.warning(
                "The LangChain agent dependencies are not available in this environment. "
                "See the README.md or docs/setup.md for installation instructions."
            )
            return

        try:
            with st.spinner("Gathering insights from Reddit and Google..."):
                logging.info(f"Agent query started: {query[:100]}")
                results = run_agent(query)
                logging.info(f"Agent query completed. Tools used: {results.get('metadata', {}).get('tools_used', [])}")
        except ImportError as exc:
            logging.error(f"Import error: {exc}")
            st.error(
                "Unable to initialize the LangChain agent. Confirm the `langchain` package "
                "matches the project's supported version or complete the agent wiring stories. "
                f"Details: {exc}"
            )
            return
        except Exception as exc:
            logging.error(f"Agent execution error: {exc}", exc_info=True)
            st.error(f"An error occurred while processing your query: {exc}")
            return

        render_results(results)

        if show_debug_panel:
            with st.expander("🔍 Debug & Logs", expanded=False):
                st.subheader("Execution Metadata")
                metadata = results.get("metadata", {})
                st.json(
                    {
                        "query": results.get("query", ""),
                        "tools_used": metadata.get("tools_used", []),
                        "execution_time_seconds": round(metadata.get("execution_time", 0), 2),
                        "total_sources_searched": metadata.get("total_sources_searched", 0),
                        "api_costs": metadata.get("api_costs", 0.0),
                    }
                )

                if "error" in results:
                    st.subheader("Error Details")
                    st.json(results["error"])

                st.subheader("View Logs")
                st.info(
                    "📝 Logs are displayed in the terminal where you ran `streamlit run app/streamlit_app.py`. "
                    "To see more detailed logs, set the environment variable:\n\n"
                    "```bash\n"
                    "export LOG_LEVEL=DEBUG\n"
                    "export AGENT_VERBOSE=true\n"
                    "export SHOW_DEBUG_PANEL=true\n"
                    "streamlit run app/streamlit_app.py\n"
                    "```"
                )


if __name__ == "__main__":
    main()
