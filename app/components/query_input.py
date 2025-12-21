"""Streamlit component for rendering the query input field."""

from __future__ import annotations

import streamlit as st

# Streamlit keys are centralized to avoid accidental collisions.
QUERY_INPUT_KEY = "query_input_text"
EXAMPLE_SELECT_KEY = "query_input_example_select"
IS_VALID_KEY = "query_input_is_valid"
WORD_COUNT_KEY = "query_input_word_count"

# Validation constraints are defined once to keep UI, tests, and downstream logic aligned.
WORD_MIN = 1
WORD_MAX = 50

# Example prompts provide fast-start options for stakeholders during demos.
EXAMPLE_PLACEHOLDER = "Need inspiration? Select a preset (optional)"
EXAMPLE_PROMPTS = [
    "Customers struggling with onboarding to the analytics dashboard",
    "Pain points developers report when calling the public API",
    "Common frustrations mentioned in support tickets about billing",
]


def normalize_query(raw_text: str) -> str:
    """Trim outer whitespace and collapse interior runs of whitespace."""

    return " ".join(raw_text.strip().split())


def count_words(clean_text: str) -> int:
    """Count the number of words in the cleaned query."""

    if not clean_text:
        return 0
    return len(clean_text.split())


def validate_query(clean_text: str) -> tuple[bool, str | None]:
    """Validate the cleaned query and return (is_valid, error_message)."""

    word_count = count_words(clean_text)
    if word_count < WORD_MIN:
        return False, "Enter at least one word so we know what to search for."
    if word_count > WORD_MAX:
        return False, f"Keep it concise—limit is {WORD_MAX} words (currently {word_count})."
    return True, None


def _apply_example_selection() -> None:
    """Copy the example prompt into the text area whenever a preset is chosen."""

    selection = st.session_state.get(EXAMPLE_SELECT_KEY)
    if not selection or selection == EXAMPLE_PLACEHOLDER:
        return

    # Copy selected preset into the text area and reset the selector so users can re-apply presets.
    st.session_state[QUERY_INPUT_KEY] = selection
    st.session_state[EXAMPLE_SELECT_KEY] = EXAMPLE_PLACEHOLDER


def render_query_input() -> str:
    """Render the query input component and return the cleaned text."""

    with st.container():
        selection = st.selectbox(
            label="Example queries",
            options=[EXAMPLE_PLACEHOLDER, *EXAMPLE_PROMPTS],
            index=0,
            key=EXAMPLE_SELECT_KEY,
            help="Use a preset if you need a quick starting point.",
        )

        raw_query = st.text_area(
            label="Describe the customer pain points you want to explore (1–50 words)",
            key=QUERY_INPUT_KEY,
            height=160,
            placeholder="Example: Customers say the reporting dashboard feels slow and confusing on mobile.",
            label_visibility="collapsed",
        )

        if selection and selection != EXAMPLE_PLACEHOLDER:
            if not raw_query.strip():
                st.session_state[QUERY_INPUT_KEY] = selection
                raw_query = selection
            st.session_state[EXAMPLE_SELECT_KEY] = EXAMPLE_PLACEHOLDER

        clean_query = normalize_query(raw_query)
        word_count = count_words(clean_query)
        st.caption(f"{word_count} / {WORD_MAX} words")

        is_valid, error_message = validate_query(clean_query)
        st.session_state[IS_VALID_KEY] = is_valid  # Downstream components can read this flag.
        st.session_state[WORD_COUNT_KEY] = word_count

        feedback = st.empty()
        if word_count == 0:
            feedback.info("Word limit is 1–50 words. Try a preset or describe the scenario in your own words.")
        elif is_valid:
            feedback.success("Ready to submit.")
        else:
            feedback.error(error_message)

    return clean_query
