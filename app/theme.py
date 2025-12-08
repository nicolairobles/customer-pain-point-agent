"""Global styling helpers for the Streamlit application."""

from __future__ import annotations

import streamlit as st

_CSS_SESSION_KEY = "_global_styles_applied"


def get_global_css() -> str:
    """Return the global CSS overrides for the Streamlit app."""

    return """
    <style>
    :root {
        --color-background: #f5f0fa;
        --color-background-gradient: radial-gradient(140% 120% at 10% 0%, #fcfbff 0%, #f0e6fb 45%, #e4d4ff 100%);
        --color-surface: rgba(239, 234, 242, 0.95);
        --color-surface-muted: rgba(239, 234, 242, 0.75);
        --color-text-primary: #2d1b3d;
        --color-text-secondary: #7a708b;
        --color-accent: #9f7aea;
        --color-accent-hover: #8157d0;
        --color-focus: #be93f7;
        --color-border: rgba(125, 109, 155, 0.25);
        --shadow-md: 0 18px 40px rgba(45, 27, 61, 0.12);
        --font-primary: "Lato", "Helvetica Neue", sans-serif;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --color-background: #120b1d;
            --color-background-gradient: radial-gradient(140% 120% at 10% 0%, #231432 0%, #1b0f29 45%, #130922 100%);
            --color-surface: rgba(45, 27, 61, 0.92);
            --color-surface-muted: rgba(45, 27, 61, 0.7);
            --color-text-primary: #efeaf2;
            --color-text-secondary: #c5bcd6;
            --color-accent: #b794f6;
            --color-accent-hover: #9f7aea;
            --color-focus: rgba(190, 147, 247, 0.55);
            --color-border: rgba(190, 147, 247, 0.25);
        }
    }

    [data-testid="stAppViewContainer"] {
        background: var(--color-background-gradient);
        color: var(--color-text-primary);
        font-family: var(--font-primary);
        padding: 32px 48px 48px;
    }

    [data-testid="stAppViewBlockContainer"] {
        padding-top: 0;
        padding-bottom: 0;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-primary);
        color: var(--color-text-primary);
    }

    .stButton>button {
        border-radius: 999px;
        background: linear-gradient(135deg, var(--color-accent) 0%, #7f56d9 100%);
        color: #ffffff;
        border: none;
        padding: 0.65rem 1.8rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        box-shadow: var(--shadow-md);
        transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.2s ease;
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 20px 50px rgba(127, 86, 217, 0.35);
        background: linear-gradient(135deg, var(--color-accent-hover) 0%, #6940ce 100%);
    }

    .stButton>button:focus {
        outline: 3px solid var(--color-focus);
        outline-offset: 2px;
    }

    .stTextInput>div>div>input, .stTextArea textarea {
        border-radius: 18px;
        border: 1px solid var(--color-border);
        padding: 0.85rem 1.15rem;
        background: #ffffff;
        font-family: var(--font-primary);
        color: var(--color-text-primary);
        box-shadow: inset 0 1px 4px rgba(45, 27, 61, 0.05);
    }

    .stTextInput>div>div>input:focus, .stTextArea textarea:focus {
        border-color: var(--color-accent);
        box-shadow: 0 0 0 3px rgba(159, 122, 234, 0.25);
    }

    div[data-baseweb="select"] > div {
        border-radius: 18px !important;
        border: 1px solid var(--color-border) !important;
        background: #ffffff !important;
        font-family: var(--font-primary);
        color: var(--color-text-primary);
    }

    .stMarkdown ul {
        padding-left: 1.25rem;
    }

    .stTabs [data-baseweb="tab-list"] {
        border-bottom: 1px solid var(--color-border);
        gap: 0.35rem;
    }

    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        border-radius: 12px 12px 0 0;
        padding: 0.7rem 1.1rem;
        font-weight: 600;
        color: var(--color-text-secondary);
    }

    .stTabs [aria-selected="true"] {
        background-color: var(--color-surface);
        color: var(--color-text-primary);
        box-shadow: 0 -1px 12px rgba(45, 27, 61, 0.08);
    }

    .stAlert {
        border-radius: 16px;
        box-shadow: var(--shadow-md);
    }

    footer {
        visibility: hidden;
    }

    section[data-testid="stSidebar"] {
        background: rgba(36, 20, 53, 0.9);
        color: #efeaf2;
    }

    section[data-testid="stSidebar"] * {
        color: inherit !important;
    }

    @media (max-width: 900px) {
        [data-testid="stAppViewContainer"] {
            padding: 24px 24px 36px;
        }

        h1 {
            font-size: 2rem;
        }

        .stButton>button {
            width: 100%;
        }
    }
    </style>
    """


def apply_global_styles() -> None:
    """Apply the global CSS overrides once per Streamlit session."""

    if st.session_state.get(_CSS_SESSION_KEY):
        return
    st.markdown(get_global_css(), unsafe_allow_html=True)
    st.session_state[_CSS_SESSION_KEY] = True

