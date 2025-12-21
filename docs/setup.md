# Project Setup Guide

This guide covers local development setup, configuration, and common troubleshooting.

## Prerequisites
- Python 3.11.x
- Git

## 1) Create and activate a virtual environment
```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 2) Install dependencies
```bash
pip install -r requirements.txt
```

## 3) Configure environment variables / secrets
Copy the example file and fill in values:
```bash
cp .env.example .env
```

Required:
- `OPENAI_API_KEY`

Optional (depending on enabled tools):
- Reddit: `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, `REDDIT_USER_AGENT`
- Google Search: `GOOGLE_SEARCH_API_KEY`, `GOOGLE_SEARCH_ENGINE_ID`

Tool flags (defaults to `true`):
- `TOOL_REDDIT_ENABLED`
- `TOOL_GOOGLE_SEARCH_ENABLED`

UI flags:
- `UI_PRODUCTION_MODE` (default `true`)
- `SHOW_DEBUG_PANEL` (default `false`)

## 4) Run the app locally
```bash
streamlit run app/streamlit_app.py
```

By default the app listens on `http://localhost:8501`.

## 5) Run tests
```bash
pytest
```

## Deployment references
- Streamlit Community Cloud: `docs/deployment/streamlit-community-cloud.md`
- Docker + GHCR workflow: `docs/deployment/production-deployment.md`

## Troubleshooting

### “Missing required secrets: …”
- Confirm the keys exist in `.env` (local) or Streamlit **Secrets** (cloud).
- If you are deploying without Google Search, set `TOOL_GOOGLE_SEARCH_ENABLED=false` and omit Google keys.

### “ModuleNotFoundError: No module named 'streamlit'”
- Ensure you activated the virtual environment (`source .venv/bin/activate`) before running `streamlit`.
- Reinstall deps: `pip install -r requirements.txt`

### Port already in use
```bash
STREAMLIT_SERVER_PORT=8502 streamlit run app/streamlit_app.py
```
