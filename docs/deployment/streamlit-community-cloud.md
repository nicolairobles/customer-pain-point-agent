# Streamlit Community Cloud Deployment (Step-by-Step)

This guide walks through deploying the Streamlit app using Streamlit Community Cloud (share.streamlit.io).

## Prerequisites
- A GitHub account with access to this repo.
- Required API credentials (at minimum `OPENAI_API_KEY`; see secrets section below).
- App entrypoint: `app/streamlit_app.py`

## 1) Create a Streamlit account
1. Go to `https://share.streamlit.io`.
2. Sign in with GitHub.

## 2) Create the Streamlit app
1. Click **New app** → **From existing repo**.
2. Select:
   - **Repository**: `nicolairobles/customer-pain-point-agent`
   - **Branch**: `development` (or `master` if you deploy from the default branch)
   - **Main file path**: `app/streamlit_app.py`
3. Click **Deploy**.

## 3) Add secrets (required)
1. Open the app page in Streamlit.
2. Click **⋯** → **Settings** → **Secrets**.
3. Paste TOML secrets like:

```toml
OPENAI_API_KEY = "..."

REDDIT_CLIENT_ID = "..."
REDDIT_CLIENT_SECRET = "..."
REDDIT_USER_AGENT = "customer-pain-point-agent"

GOOGLE_SEARCH_API_KEY = "..."
GOOGLE_SEARCH_ENGINE_ID = "..."

TOOL_REDDIT_ENABLED = "true"
TOOL_GOOGLE_SEARCH_ENABLED = "true"

UI_PRODUCTION_MODE = "true"
SHOW_DEBUG_PANEL = "false"
```

4. Click **Save**. Streamlit will restart the app.

Notes:
- This repo supports reading Streamlit secrets and mapping them into environment variables during startup (`config/settings.py`), so the rest of the code can keep using `os.getenv(...)`.
- If you disable a tool, you can omit its keys.

## 4) Deploying without Google Search (optional mode)
If you do not want Google Search in production, set:

```toml
TOOL_GOOGLE_SEARCH_ENABLED = "false"
```

Then you can omit `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID`.

## 5) Verify and troubleshoot
1. Open the deployed app URL.
2. Run a query and confirm the report renders.
3. If something fails:
   - Use the app page → **Manage app** to view logs.
   - Confirm Secrets are saved and correctly named.
   - Confirm the configured branch contains `runtime.txt` and pinned `requirements.txt`.

