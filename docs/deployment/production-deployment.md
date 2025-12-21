# Production Deployment Runbook

This guide documents how to ship the Streamlit application to production, monitor its health, and recover quickly if a release misbehaves. The workflow is container-first to keep Python 3.11 and `langchain` pins consistent with `requirements.txt`.

## Automation overview

- **Dockerfile** (repo root) builds a slim Python 3.11 image, installs pinned dependencies, and runs the Streamlit app on port `8501` with a built-in health check.
- **GitHub Actions workflow**: `.github/workflows/deploy.yml` builds the image, runs the test suite, and publishes to GitHub Container Registry (`ghcr.io`).
  - Triggers on `master` updates (app/config changes) and via **workflow_dispatch** for manual deploys.
  - Uses `actions/setup-python@v5` to ensure the Python 3.11 toolchain matches production.
  - Tags images with the commit SHA by default; override via the `image_tag` input when dispatching the workflow.

## Required secrets and configuration

Set these as environment secrets in your hosting platform (or GitHub Actions environment if you add a deploy step there). Never commit real values to source control.

| Variable | Purpose | Required |
| --- | --- | --- |
| `OPENAI_API_KEY` | LLM requests | Yes |
| `REDDIT_CLIENT_ID` / `REDDIT_CLIENT_SECRET` | Reddit API credentials | Yes (when `TOOL_REDDIT_ENABLED=true`) |
| `REDDIT_USER_AGENT` | Identifies client to Reddit | Recommended |
| `GOOGLE_SEARCH_API_KEY` / `GOOGLE_SEARCH_ENGINE_ID` | Google Custom Search | Yes (when `TOOL_GOOGLE_SEARCH_ENABLED=true`) |
| `TWITTER_BEARER_TOKEN` | Reserved for future Twitter ingestion | Optional |
| `STREAMLIT_SERVER_PORT` | Overrides default port | Optional |

The container healthcheck validates secrets based on enabled tools:
- If `TOOL_REDDIT_ENABLED=true` (default), it requires Reddit credentials.
- If `TOOL_GOOGLE_SEARCH_ENABLED=true` (default), it requires Google credentials.
Disable a tool explicitly (set the env var to `false`) if you deploy without that provider.

For GitHub Actions publishing, `GITHUB_TOKEN` (provided by GitHub) authenticates to GHCR. Deploy-time secrets should be injected by the runtime (Kubernetes/VM host/Streamlit Community Cloud) rather than stored in the image.

## Deploying a new release

### Using GitHub Actions (recommended)
1. Navigate to **Actions → Deploy Streamlit app → Run workflow**.
2. Optionally set `image_tag` (e.g., `v1.0.0` or a release branch name); otherwise the commit SHA is used.
3. The workflow will:
   - Install dependencies and run `pytest`.
   - Build `ghcr.io/<owner>/<repo>:<tag>` and `:latest` from the root `Dockerfile`.
   - Push both tags to GHCR.
4. Pull the tagged image in your hosting environment and start it with an env file containing the required secrets (example below).

### Manual fallback (no CI/CD available)
```bash
docker build -t ghcr.io/your-org/customer-pain-point-agent:manual .
docker run -d --env-file .env --name pain-points -p 8501:8501 ghcr.io/your-org/customer-pain-point-agent:manual
```
If you cannot use containers, run the app directly:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/streamlit_app.py
```

## Health checks and monitoring

- The container `HEALTHCHECK` runs `scripts/healthcheck.py` against `http://localhost:8501/` to ensure the app is reachable and secrets are present.
- External uptime monitors (Pingdom, UptimeRobot, Streamlit status page) should hit `https://<your-host>/` and alert a dedicated Slack/email channel.
- To probe from CI or a runbook, use:
```bash
python scripts/healthcheck.py --url https://<your-host>/ --timeout 10 --allow-missing-secrets
```
  - Omit `--allow-missing-secrets` in production to fail fast if credentials disappear.

## Rollback plan

1. Identify the last good image tag (previous release tag or commit SHA) in GHCR.
2. Re-run the **Deploy Streamlit app** workflow with `image_tag` set to that tag **or** redeploy the host to pull the prior tag.
3. If the regression is dependency-related, revert the offending commit in `requirements.txt`/`Dockerfile` and redeploy.
4. Flush Streamlit caches after rollback:
   - Container: restart the container; the cache lives in the container filesystem and clears on restart.
   - VM/manual: remove `~/.streamlit/cache` and restart the process.
5. Document the incident and follow up with a postmortem if monitors fired.

## Smoke testing and drills

- After deployment, run a quick query in the UI and confirm results load; capture a screenshot for the release log.
- Use `scripts/healthcheck.py` against the public host to verify uptime monitors match container health.
- Disaster-recovery practice: stop the container/process, confirm alerts fire, then redeploy the last good image within 15 minutes.
