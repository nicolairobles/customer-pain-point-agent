"""Quick Streamlit preview for the results display component.

Serves a fixed payload so designers/testers can exercise the UI without invoking
the full LangChain agent stack (which currently requires additional refactoring).
"""

from __future__ import annotations

import pathlib
import sys

import streamlit as st

# Ensure repository root is on sys.path when run via `streamlit run scripts/...`
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.components.results_display import render_results
from app.theme import apply_global_styles


SAMPLE_RESULTS = {
    "pain_points": [
        {
            "name": "Slow dashboard exports",
            "description": (
                "Customers report that exporting CSVs from the analytics dashboard takes several minutes "
                "or times out entirely during peak usage windows. Requests against the /export endpoint "
                "often exceed five minutes."
            ),
            "frequency": 12,
            "examples": [
                "Export spins forever on Chrome",
                "‘Generate report’ times out when the dataset is >50k rows",
            ],
            "sources": [
                {"platform": "Reddit", "url": "https://reddit.com/r/api/comments/example"},
                {"title": "Support Ticket #42"},
            ],
        },
        {
            "name": "Confusing billing flow",
            "description": (
                "Users struggle to locate detailed invoices and usage breakdowns. The hierarchy between "
                "teams and workspaces is unclear, leading to accidental overages."
            ),
            "frequency": "high (qualitative)",
            "examples": ["Where do I see usage per team?", "Invoice split between sandboxes is confusing"],
            "sources": [{"platform": "Google Search", "url": "https://example.com/discussion/123"}],
        },
    ],
    "metadata": {
        "total_sources_searched": 18,
        "execution_time": 1.832,
        "api_costs": 0.0075,
    },
    "warnings": ["Google Search API quota hit; showing partial results."],
}


def main() -> None:
    st.set_page_config(page_title="Results Preview", layout="wide")
    apply_global_styles()
    st.title("Results Component Preview")
    st.write(
        "This preview renders the 1.4.3 results display with a fixed payload so you can inspect styling "
        "and responsiveness without running the full agent."
    )
    render_results(SAMPLE_RESULTS)


if __name__ == "__main__":
    main()
