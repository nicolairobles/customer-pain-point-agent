"""Global styling helpers for the Streamlit application."""

from __future__ import annotations

import streamlit as st


def get_global_css() -> str:
    """Return the global CSS overrides for the Streamlit app."""

    return """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600&display=swap');
    :root {
        --color-background: #ffffff;
        /* Keep backgrounds mostly whitespace; use a barely-there tint for depth. */
        --color-background-gradient: linear-gradient(180deg, #ffffff 0%, #fbfbfe 100%);
        --color-surface: rgba(255, 255, 255, 0.72);
        --color-surface-muted: rgba(255, 255, 255, 0.60);
        --color-text-primary: #141025;
        --color-text-secondary: rgba(20, 16, 37, 0.62);
        --color-accent: #7f56d9;
        --color-accent-hover: #6a46c5;
        --color-focus: rgba(127, 86, 217, 0.35);
        --color-border: rgba(20, 16, 37, 0.10);
        --shadow-md: 0 18px 40px rgba(20, 16, 37, 0.10);
        --font-primary: "Inter", ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
    }

    /* Force light-mode styling even when OS/browser prefers dark. */
    :root {
        color-scheme: light;
    }

    html, body {
        font-family: var(--font-primary);
        font-weight: 300;
        color-scheme: light;
    }

    [data-testid="stAppViewContainer"] {
        background: var(--color-background);
        /* Minimalist, Attio-like depth without loud gradients. */
        background-image:
            radial-gradient(900px 520px at 18% 10%, rgba(127, 86, 217, 0.06) 0%, rgba(127, 86, 217, 0.0) 60%),
            radial-gradient(900px 520px at 82% 28%, rgba(127, 86, 217, 0.04) 0%, rgba(127, 86, 217, 0.0) 62%);
        color: var(--color-text-primary);
        font-family: var(--font-primary);
        padding: 24px 48px 48px;
        color-scheme: light;
    }

    /* Force Inter across Streamlit/BaseWeb widgets (keep monospace for code blocks). */
    [data-testid="stAppViewContainer"] * {
        font-family: var(--font-primary) !important;
        font-weight: 300;
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
    [data-testid="stMainBlockContainer"] {
        padding: 0 1.5rem 1.5rem;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: var(--font-primary);
        color: var(--color-text-primary);
        font-weight: 500;
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
    button[data-testid^="stBaseButton-secondary"] {
        background: #ffffff !important;
        color: var(--color-text-primary) !important;
        border: 1px solid var(--color-border) !important;
        box-shadow: 0 8px 20px rgba(20, 16, 37, 0.08);
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
    div[data-baseweb="select"] input {
        color: var(--color-text-primary) !important;
    }
    div[data-baseweb="popover"] {
        background: #ffffff !important;
        color: var(--color-text-primary) !important;
        border-radius: 14px;
        box-shadow: 0 14px 30px rgba(20, 16, 37, 0.10);
    }
    ul[role="listbox"] {
        background: #ffffff !important;
        color: var(--color-text-primary) !important;
    }
    li[role="option"] {
        color: var(--color-text-primary) !important;
    }

    .stMarkdown ul {
        padding-left: 1.25rem;
    }

    .pp-wordmark {
        font-size: 0.9rem;
        font-weight: 500;
        letter-spacing: 0.28em;
        text-transform: uppercase;
        color: var(--color-text-secondary);
        margin: 0;
    }

    .pp-header-bar {
        position: sticky;
        top: 0;
        z-index: 5;
        padding: 8px 0 12px;
        margin-bottom: 8px;
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
        font-weight: 500;
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
        background: rgba(255, 255, 255, 0.78);
        border-right: 1px solid rgba(20, 16, 37, 0.08);
    }

    /* Research progress panel (Perplexity-inspired) */
    .pp-panel {
        /* Minimal gradient-border glassmorphism */
        background: linear-gradient(135deg, rgba(127, 86, 217, 0.22) 0%, rgba(127, 86, 217, 0.06) 55%, rgba(255, 255, 255, 0.0) 100%);
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
        font-weight: 500;
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
        width: 10px;
        height: 10px;
        border-radius: 999px;
        background: rgba(20, 16, 37, 0.22);
        box-shadow: 0 0 0 1px rgba(20, 16, 37, 0.08);
    }

    .pp-chips { display: none; }

    @keyframes ppPulseGlow {
        0% {
            box-shadow: 0 0 0 3px rgba(127, 86, 217, 0.08), 0 0 0 0 rgba(127, 86, 217, 0.0);
            border-color: rgba(127, 86, 217, 0.26);
        }
        50% {
            box-shadow: 0 0 0 3px rgba(127, 86, 217, 0.14), 0 0 22px rgba(127, 86, 217, 0.18);
            border-color: rgba(127, 86, 217, 0.42);
        }
        100% {
            box-shadow: 0 0 0 3px rgba(127, 86, 217, 0.08), 0 0 0 0 rgba(127, 86, 217, 0.0);
            border-color: rgba(127, 86, 217, 0.26);
        }
    }

    .pp-step--active {
        border-color: rgba(127, 86, 217, 0.35);
        background: linear-gradient(135deg, rgba(127, 86, 217, 0.10) 0%, rgba(34, 211, 238, 0.10) 100%);
    }

    @keyframes ppDotPulse {
        0% {
            opacity: 0.55;
            box-shadow:
                0 0 0 1px rgba(127, 86, 217, 0.18),
                0 0 0 0 rgba(127, 86, 217, 0.0);
            transform: scale(0.98);
        }
        50% {
            opacity: 1;
            box-shadow:
                0 0 0 1px rgba(127, 86, 217, 0.34),
                0 0 18px rgba(127, 86, 217, 0.35),
                0 0 26px rgba(127, 86, 217, 0.22);
            transform: scale(1.12);
        }
        100% {
            opacity: 0.55;
            box-shadow:
                0 0 0 1px rgba(127, 86, 217, 0.18),
                0 0 0 0 rgba(127, 86, 217, 0.0);
            transform: scale(0.98);
        }
    }

    .pp-step--active .pp-step-dot {
        background: linear-gradient(135deg, rgba(127, 86, 217, 0.88) 0%, rgba(127, 86, 217, 0.62) 100%);
        filter: drop-shadow(0 0 10px rgba(127, 86, 217, 0.20));
        animation: ppDotPulse 1.15s ease-in-out infinite;
    }

    .pp-step--done {
        opacity: 0.75;
    }

    .pp-step--done .pp-step-dot {
        background: rgba(127, 86, 217, 0.65);
        box-shadow: 0 0 0 1px rgba(127, 86, 217, 0.20);
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
        font-weight: 500;
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
        grid-template-columns: 1fr 2fr;
        gap: 10px;
        padding: 6px 0;
        align-items: center;
    }

    .pp-source-row-domain {
        font-weight: 500;
    }

    .pp-source-row-title {
        color: var(--color-text-secondary);
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }

    .pp-activity { display: none; }

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
