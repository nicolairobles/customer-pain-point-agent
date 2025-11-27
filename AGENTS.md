# Repository Guidelines

## Project Structure & Module Organization
- Core code lives in `src/`: `agent/` (LangChain orchestration), `tools/` (Reddit, Twitter, Google Search integrations), `extractors/` (OpenAI JSON parsing), and `utils/` (validation/formatting). Configuration defaults sit in `config/settings.py`.
- UI is a Streamlit app at `app/streamlit_app.py`; docs and architecture notes live in `docs/`. Example outputs and ad-hoc scripts sit in `examples/` and `scripts/`.
- Tests follow `tests/test_*.py`. Keep fixtures and sample payloads close to the feature under test.

## Build, Test, and Development Commands
- Create a local env and install deps (Python 3.11): `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`.
- Seed configuration: `cp .env.example .env` then fill API keys (OpenAI, Reddit, Twitter, Google Search).
- Run the dashboard: `streamlit run app/streamlit_app.py`.
- Quick tool smoke tests: `python scripts/run_reddit_tool_debug.py --query "your topic"` and `python scripts/test_google_search.py` (requires Google keys).
- Full test suite: `pytest`; add `-k` to target modules while iterating.

## Coding Style & Naming Conventions
- Python: 4-space indentation, snake_case for functions/variables, PascalCase for classes; prefer explicit type hints on public functions.
- Keep LangChain tool inputs/outputs typed and JSON-serializable; mirror existing pydantic models when adding new fields.
- Follow existing module patterns (e.g., orchestrators in `src/agent`, API clients in `src/tools`); colocate helper functions with their feature area rather than adding new globals.

## Testing Guidelines
- Add/extend `tests/test_*.py` alongside new features; prefer deterministic unit tests over network calls—mock API clients where possible.
- For integration checks that need real credentials, guard with environment checks so CI can skip gracefully.
- When adding extractors, include shape assertions for JSON schemas and minimal examples under `tests/fixtures` or inline sample payloads.

## Commit & Pull Request Guidelines
- Commit messages are imperative; semantic prefixes like `fix(...)` or `chore(...)` are common but optional—keep the scope focused (e.g., `fix(google_search): handle missing credentials`).
- PRs should explain the user impact, note required env vars or migrations, and link related issues. Include before/after notes or screenshots for UI changes and sample JSON for new tool outputs.
- Call out any new external calls or rate-limit considerations in the description so reviewers can validate safely.

## Security & Configuration Tips
- Never commit real API keys; `.env.example` is the only place to document required settings. Use test keys for examples.
- If adding new providers, thread credentials through `config/settings.py` and document required vars in both the config defaults and this guide.
