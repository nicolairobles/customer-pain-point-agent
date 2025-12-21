# Customer Pain Point Discovery Agent

An AI-powered agent that aggregates customer pain points from Reddit and Google Search, extracts structured insights, and presents them in a Streamlit dashboard.

## Features
- Natural language query interface (1-50 words)
- Multi-source search across Reddit and Google Search
- LLM-powered pain point extraction with structured JSON output
- Streamlit dashboard for interactive exploration
- Modular architecture for adding new data sources

## Getting Started

### Prerequisites
- Python 3.11.x (project pinned to `langchain==0.0.340`; macOS users can bootstrap Miniforge and create `conda create -n cppagent-py311 python=3.11`)
- Access credentials for Reddit, Google Search APIs, and OpenAI

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` and populate the required API keys.

### Running the App
```bash
streamlit run app/streamlit_app.py
```

### Testing
```bash
pytest
```

## Deployment
- **Automated (recommended):** Dispatch `Deploy Streamlit app` in GitHub Actions to build and publish a Docker image to GHCR using Python 3.11 and the pinned dependencies. Configure your host to pull `ghcr.io/<owner>/customer-pain-point-agent:<tag>` and inject secrets via environment variables (see `.env.example`).
- **Manual fallback:** `docker build -t ghcr.io/your-org/customer-pain-point-agent:manual .` then `docker run -d --env-file .env -p 8501:8501 ghcr.io/your-org/customer-pain-point-agent:manual`. For VM installs, activate a venv and run `streamlit run app/streamlit_app.py`.
- **Monitoring & rollback:** The container `HEALTHCHECK` runs `scripts/healthcheck.py` against `/`. Wire an external monitor (Pingdom/UptimeRobot) to the public URL and alert Slack/email. To rollback, redeploy the previous GHCR tag or revert dependency changes and re-run the workflow; restarting the container clears Streamlit caches.

See `docs/deployment/production-deployment.md` for the full runbook.

## Project Structure
Refer to `docs/architecture.md` for detailed architectural guidance.

## **Reddit Tool Example**

**Example Output File**: `examples/reddit_tool_example_output.json` — a saved, sanitized sample of `RedditTool` output.

### Quick Run (debug) 
Prints sanitized JSON to stdout. 
```bash
python scripts/run_reddit_tool_debug.py
```
### Quick Run (debug) With sample output
```bash
python scripts/run_reddit_tool_debug.py > examples/debug_output.json
``` 
### Quick Run (CLI) 
```bash
python scripts/run_reddit_tool_cli.py --query "python decorators" --subreddits python --limit 3 --per-subreddit 3 --time-filter week
``` 

**Usage Notes**: Ensure you have populated `.env` from `.env.example` with `REDDIT_CLIENT_ID`, `REDDIT_CLIENT_SECRET`, and `REDDIT_USER_AGENT` before running the scripts.

**Fields in the example output**: each item contains the following keys: `id`, `title`, `text`, `upvotes`, `comments`, `url`, `subreddit`, `timestamp`.

See `examples/reddit_tool_example_output.json` for a concrete sample.
