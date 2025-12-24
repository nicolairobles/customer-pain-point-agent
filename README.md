# Customer Pain Point Discovery Agent

An applied AI agent that turns noisy Reddit + Google chatter into validated pain points with citations. Outputs stay aligned across JSON (for automation) and narrative (for humans), and render in a Streamlit UI.

## Quick context
- **Who it’s for:** PMs, researchers, hiring managers needing fast signal.
- **What it delivers:** Deduped pain points with evidence, severity, and citations; JSON + narrative share the same sources.
- **Runtime target:** &lt; 90s query-to-report under typical loads.
- **Sources:** Reddit (PRAW) and Google Custom Search; feature flags let you toggle providers.

## How it works (overview)
- **Intake:** Streamlit UI enforces sane query length and presets.
- **Orchestration:** LangChain sequences tool calls and streams progress.
- **Retrieval:** Reddit + Google results normalized into one schema.
- **Aggregation:** Merge near-duplicates while preserving URLs/subreddits/timestamps.
- **Extraction:** OpenAI prompt emits schema-validated JSON (Pydantic guards malformed outputs).
- **Reporting:** JSON + narrative surfaced together with citations and runtime metrics.

## Stack
- Streamlit UI
- LangChain orchestration
- OpenAI extraction
- PRAW + Google Custom Search
- Pydantic contracts
- Pytest + GitHub Actions

## Getting Started

### Prerequisites
- Python 3.11.x (deployment pins via `runtime.txt` and `requirements.txt`)
- Credentials for Reddit, Google Search APIs, and OpenAI

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` and populate API keys and secrets (Reddit, Google CSE, OpenAI).

### Run the app
```bash
streamlit run app/streamlit_app.py
```

### Testing
```bash
pytest
```

## Deployment
- **Automated (recommended):** Dispatch `Deploy Streamlit app` GitHub Action to build and push a Docker image to GHCR (`ghcr.io/<owner>/customer-pain-point-agent:<tag>`). Inject secrets via environment variables (use `.env.example` as the source of truth).
- **Manual fallback:** `docker build -t ghcr.io/your-org/customer-pain-point-agent:manual .` then `docker run -d --env-file .env -p 8501:8501 ghcr.io/your-org/customer-pain-point-agent:manual`. For VM installs, activate a venv and run `streamlit run app/streamlit_app.py`.
- **Monitoring & rollback:** Container `HEALTHCHECK` runs `scripts/healthcheck.py` against `/`. Wire an external monitor (Pingdom/UptimeRobot) to the public URL and alert Slack/email. To rollback, redeploy the previous GHCR tag or revert dependency changes and re-run the workflow; restarting the container clears Streamlit caches.

See `docs/deployment/production-deployment.md` for the full runbook.

## Project Structure & Docs
- Architecture: `docs/architecture.md`
- Setup: `docs/setup.md`
- User guide: `docs/user-guide.md`
- Deployment runbook: `docs/deployment/production-deployment.md`

## Reddit Tool example

**Example output file:** `examples/reddit_tool_example_output.json` (sanitized `RedditTool` output).

### Quick run (debug)
```bash
python scripts/run_reddit_tool_debug.py
```

### Quick run (debug) with sample output
```bash
python scripts/run_reddit_tool_debug.py > examples/debug_output.json
```

### Quick run (CLI)
```bash
python scripts/run_reddit_tool_cli.py --query "python decorators" --subreddits python --limit 3 --per-subreddit 3 --time-filter week
```

**Usage notes:** Populate `.env` from `.env.example` with `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and `REDDIT_USER_AGENT` before running scripts.

**Fields in the example output:** `id`, `title`, `text`, `upvotes`, `comments`, `url`, `subreddit`, `timestamp`.

See `examples/reddit_tool_example_output.json` for a concrete sample.
