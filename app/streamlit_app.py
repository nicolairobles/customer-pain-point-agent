"""Streamlit entry point for the Customer Pain Point Discovery Agent."""

from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from queue import Empty, Queue
import streamlit as st

# Ensure repo root is on sys.path so `from src...` imports work when
# running via `streamlit run` (Streamlit changes the CWD/import path).
import sys
import pathlib
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.validators import ValidationError, validate_query_length
from app.components.query_input import render_query_presets, render_query_text_area
from app.components.research_progress import ResearchProgressPanel
from app.components.results_display import render_results
from app.theme import apply_global_styles
from config.settings import settings
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
    st.markdown(
        "<div class='pp-header-bar'><div class='pp-wordmark'>CPP Agent</div></div>",
        unsafe_allow_html=True,
    )
    st.title("Customer Pain Point Discovery Agent")

    st.markdown(
        "[GitHub repo](https://github.com/nicolairobles/customer-pain-point-agent) · "
        "[Project page](https://nicolairobles.github.io/customer-pain-point-agent)",
        help="Links to the source repository and the public project page",
    )

    render_query_presets()

    with st.form("analyze_form", clear_on_submit=False, border=False):
        query = render_query_text_area()
        submitted = st.form_submit_button("Analyze")

    show_debug_panel = (not settings.ui.production_mode) or settings.ui.debug_panel_enabled

    if submitted:
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

        progress_events: "Queue[dict]" = Queue()

        def on_progress(event: dict) -> None:
            progress_events.put(event)

        progress_panel = ResearchProgressPanel()

        try:
            logging.info("Agent query started: %s", query[:100])
            with ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(run_agent, query, progress_callback=on_progress)

                while not future.done():
                    try:
                        event = progress_events.get(timeout=0.15)
                        if isinstance(event, dict):
                            progress_panel.apply_event(event)
                    except Empty:
                        # Re-rendering without new events risks "fake" progress; keep the last real status.
                        pass
                    progress_panel.tick()
                    time.sleep(0.05)

                results = future.result()
                # Flush any remaining progress events, then force a final completion render.
                while True:
                    try:
                        event = progress_events.get_nowait()
                    except Empty:
                        break
                    if isinstance(event, dict):
                        progress_panel.apply_event(event)
                progress_panel.apply_event({"type": "stage", "stage": "complete", "message": "Done."})
                logging.info("Agent query completed. Tools used: %s", results.get("metadata", {}).get("tools_used", []))
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
                    "export UI_PRODUCTION_MODE=false\n"
                    "export SHOW_DEBUG_PANEL=true\n"
                    "streamlit run app/streamlit_app.py\n"
                    "```"
                )


if __name__ == "__main__":
    main()
