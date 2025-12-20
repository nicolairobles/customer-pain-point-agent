# Architecture Overview

## High-Level Flow
1. Streamlit UI collects user query.
2. Agent orchestrator validates input and dispatches LangChain tools.
3. Reddit and Google Search tools fetch raw conversational data.
4. Extractor module aggregates and normalizes documents via OpenAI.
5. Results are deduplicated, categorized, and rendered in the dashboard.

## Key Modules
- `src/agent`: LangChain agent orchestration and execution.
- `src/tools`: Integrations with external data sources.
- `src/extractors`: OpenAI-based extraction logic and schemas.
- `src/utils`: Cross-cutting helpers for validation and formatting.
- `app`: Streamlit application UI components.

## LangChain Agent Initialization
- Builder: `src/agent/orchestrator.build_agent_executor(settings)` creates a lightweight runner that uses LangChain's ReAct agent (`create_react_agent`) plus the project tools.
- Controls: `agent.max_iterations` and `agent.verbose` configurable via `config/settings.py` / environment variables.
- Interfaces: `invoke` and `stream` exposed through `run_agent` / `stream_agent` wrappers for batch and interactive flows.

## Reddit Tool Interface
- Entry point: `RedditTool.run({...})` / `RedditTool._run(query, subreddits, limit, per_subreddit, time_filter)` returns a list of normalized dictionaries.
- Output schema fields: `id`, `title`, `text`, `url`, `author`, `subreddit`, `created_at`, `upvotes`, `comments`, `platform`.
- Behavior: searches subreddits concurrently, caps totals via `limit`/`per_subreddit`, sorts by relevance (score + comments), retries with backoff on errors, and returns an empty list on persistent failures while logging diagnostics.
- Configuration: credentials provided via `Settings.api.reddit_client_id` and `Settings.api.reddit_client_secret`; optional `REDDIT_USER_AGENT` env var overrides default.

## Google Search Tool Interface
- Entry point: `GoogleSearchTool.run({...})` / `GoogleSearchTool._run(query, num, lang, site)` returns a list of normalized dictionaries.
- Output schema fields: `id`, `title`, `text`, `url`, `display_url`, `created_at`, `platform`, `ranking_position`, `search_metadata`.
- Behavior: caps results via `num` (max 10), sanitizes text, normalizes optional publication dates, and returns an empty list when disabled or when credentials are missing.
- Configuration: credentials provided via `Settings.api.google_search_api_key` and `Settings.api.google_search_engine_id`; enablement via `Settings.tools.google_search_enabled`.

## Non-Functional Considerations
- Environment-driven configuration loaded via `config.settings`.
- Caching and retry strategies to be implemented within tool modules.
- Logging and cost tracking to be added around API interactions.
