"""Global styling helpers for the Streamlit application."""

from __future__ import annotations

import streamlit as st


def get_global_css() -> str:
    """Return the global CSS overrides for the Streamlit app."""

    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    :root {
        --color-background: #fbfbfe;
        --color-background-gradient: radial-gradient(120% 140% at 10% 0%, #ffffff 0%, #f6f7ff 42%, #f1eaff 100%);
        --color-surface: rgba(255, 255, 255, 0.62);
        --color-surface-muted: rgba(255, 255, 255, 0.46);
        --color-text-primary: #141025;
        --color-text-secondary: rgba(20, 16, 37, 0.62);
        --color-accent: #7f56d9;
        --color-accent-hover: #6a46c5;
        --color-focus: rgba(127, 86, 217, 0.35);
        --color-border: rgba(20, 16, 37, 0.10);
        --color-neon: #22d3ee;
        --shadow-md: 0 18px 40px rgba(20, 16, 37, 0.10);
        --font-primary: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
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

    html, body {
        font-family: var(--font-primary);
        font-weight: 400;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--color-background-gradient);
        color: var(--color-text-primary);
        font-family: var(--font-primary);
        padding: 32px 48px 48px;
    }

    /* Force Inter across Streamlit/BaseWeb widgets (keep monospace for code blocks). */
    [data-testid="stAppViewContainer"] * {
        font-family: var(--font-primary) !important;
        font-weight: 400;
    }
    [data-testid="stAppViewContainer"] code,
    [data-testid="stAppViewContainer"] pre,
    [data-testid="stAppViewContainer"] kbd,
    [data-testid="stAppViewContainer"] samp {
        font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace !important;
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
        font-weight: 600;
    }

    .stButton>button {
        border-radius: 999px;
        background: linear-gradient(135deg, var(--color-accent) 0%, #7f56d9 100%);
        color: #ffffff;
        border: none;
        padding: 0.65rem 1.8rem;
        font-weight: 500;
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
        background: rgba(255, 255, 255, 0.75);
        font-family: var(--font-primary);
        color: var(--color-text-primary);
        box-shadow: inset 0 1px 4px rgba(45, 27, 61, 0.05);
    }

    .stTextInput>div>div>input:focus, .stTextArea textarea:focus {
        border-color: var(--color-accent);
        box-shadow: 0 0 0 3px rgba(159, 122, 234, 0.25);
    }

    /* BaseWeb wrappers (Streamlit form + widgets) */
    div[data-baseweb="textarea"] > div {
        border-radius: 18px !important;
        border: 1px solid var(--color-border) !important;
        background: #ffffff !important;
        box-shadow: inset 0 1px 4px rgba(45, 27, 61, 0.05) !important;
        font-family: var(--font-primary) !important;
    }

    div[data-baseweb="textarea"] > div:focus-within {
        border-color: var(--color-accent) !important;
        box-shadow: 0 0 0 3px rgba(159, 122, 234, 0.25) !important;
    }

    div[data-baseweb="textarea"] textarea {
        border-radius: 18px !important;
        background: transparent !important;
        font-family: var(--font-primary) !important;
    }

    div[data-baseweb="select"] > div {
        border-radius: 18px !important;
        border: 1px solid var(--color-border) !important;
        background: #ffffff !important;
        font-family: var(--font-primary) !important;
        color: var(--color-text-primary);
    }

    .stMarkdown ul {
        padding-left: 1.25rem;
    }

    /* Forms: avoid extra border/padding causing "boxed" look */
    [data-testid="stForm"] {
        border: none;
        padding: 0;
        background: transparent;
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

    /* Hide Streamlit's built-in deploy control / toolbar affordances */
    [data-testid="stToolbar"] {
        display: none;
    }
    [data-testid="stToolbarActions"] {
        display: none;
    }
    [data-testid="stDeployButton"] {
        display: none;
    }
    button[title="Deploy"], button[aria-label="Deploy"] {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.75) 0%, rgba(241, 234, 255, 0.65) 100%);
        border-right: 1px solid rgba(20, 16, 37, 0.08);
    }

    /* Research progress panel (Perplexity-inspired) */
    .pp-panel {
        background: linear-gradient(135deg, rgba(127, 86, 217, 0.25) 0%, rgba(34, 211, 238, 0.22) 55%, rgba(0, 245, 255, 0.18) 100%);
        border-radius: 18px;
        padding: 1px;
        margin-bottom: 14px;
    }

    .pp-panel-inner {
        background: var(--color-surface);
        border-radius: 17px;
        padding: 16px 18px;
        box-shadow: var(--shadow-md);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
    }

    .pp-progress {
        display: none;
    }

    .pp-progress-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        margin-bottom: 10px;
    }

    .pp-progress-title {
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    .pp-progress-eta {
        font-size: 0.9rem;
        color: var(--color-text-secondary);
    }

    .pp-progress-status {
        font-size: 1.02rem;
        color: var(--color-text-primary);
    }

    .pp-steps {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 10px 0 12px;
    }

    .pp-step {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        border-radius: 999px;
        border: 1px solid rgba(20, 16, 37, 0.10);
        background: rgba(255, 255, 255, 0.55);
        font-size: 0.92rem;
        font-weight: 500;
    }

    .pp-step-dot {
        width: 8px;
        height: 8px;
        border-radius: 999px;
        background: rgba(20, 16, 37, 0.18);
        box-shadow: inset 0 0 0 1px rgba(20, 16, 37, 0.12);
    }

    .pp-chips {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin: 10px 0 12px;
    }

    .pp-chip {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 10px;
        border-radius: 999px;
        border: 1px solid rgba(20, 16, 37, 0.10);
        background: rgba(255, 255, 255, 0.55);
        font-size: 0.92rem;
        font-weight: 500;
    }

    .pp-chip--running {
        border-color: rgba(34, 211, 238, 0.35);
        box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.10);
    }

    .pp-chip--done {
        opacity: 0.85;
    }

    .pp-chip--error {
        border-color: rgba(239, 68, 68, 0.30);
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.10);
    }

    .pp-chip-count {
        padding: 2px 8px;
        border-radius: 999px;
        border: 1px solid rgba(20, 16, 37, 0.10);
        background: rgba(127, 86, 217, 0.10);
        font-size: 0.82rem;
        font-weight: 600;
    }

    .pp-step--active {
        border-color: rgba(127, 86, 217, 0.35);
        box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.12);
        background: linear-gradient(135deg, rgba(127, 86, 217, 0.10) 0%, rgba(34, 211, 238, 0.10) 100%);
    }

    .pp-step--active .pp-step-dot {
        background: var(--color-accent);
        box-shadow: 0 0 0 3px rgba(127, 86, 217, 0.12);
    }

    .pp-step--done {
        opacity: 0.75;
    }

    .pp-progress-source {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        align-items: baseline;
        padding: 12px 14px;
        border-radius: 16px;
        border: 1px solid rgba(20, 16, 37, 0.08);
        background: rgba(255, 255, 255, 0.50);
        margin-bottom: 10px;
    }

    .pp-progress-source--empty {
        color: var(--color-text-secondary);
    }

    .pp-progress-source--done {
        color: var(--color-text-secondary);
    }

    .pp-source-domain {
        font-weight: 600;
        color: var(--color-accent);
    }

    .pp-source-title {
        color: var(--color-text-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
        max-width: 68ch;
    }

    .pp-sources {
        background: rgba(255, 255, 255, 0.50);
        border: 1px solid rgba(20, 16, 37, 0.08);
        border-radius: 16px;
        padding: 12px 14px;
    }

    .pp-sources-title {
        font-size: 0.9rem;
        color: var(--color-text-secondary);
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .pp-source-row {
        display: grid;
        grid-template-columns: 26px 1fr 2fr;
        gap: 10px;
        padding: 6px 0;
        align-items: center;
    }

    .pp-source-chip {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 22px;
        height: 22px;
        border-radius: 8px;
        background: rgba(127, 86, 217, 0.10);
        border: 1px solid rgba(127, 86, 217, 0.18);
    }

    .pp-source-row-domain {
        font-weight: 600;
    }

    .pp-source-row-title {
        color: var(--color-text-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .pp-activity {
        background: rgba(255, 255, 255, 0.46);
        border: 1px solid rgba(20, 16, 37, 0.08);
        border-radius: 16px;
        padding: 12px 14px;
        margin-top: 10px;
    }

    .pp-activity-title {
        font-size: 0.9rem;
        color: var(--color-text-secondary);
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    .pp-activity-row {
        display: block;
        padding: 6px 0;
    }

    .pp-activity-text {
        color: var(--color-text-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
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
    """Apply the global CSS overrides for the current render."""
    st.markdown(get_global_css(), unsafe_allow_html=True)
