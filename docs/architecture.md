# Architecture Overview

## High-Level Flow
1. Streamlit UI collects user query.
2. Agent orchestrator validates input and dispatches LangChain tools.
3. Reddit, Twitter, and Google Search tools fetch raw conversational data.
4. Extractor module aggregates and normalizes documents via OpenAI.
5. Results are deduplicated, categorized, and rendered in the dashboard.

## Key Modules
- `src/agent`: LangChain agent orchestration and execution.
- `src/tools`: Integrations with external data sources.
- `src/extractors`: OpenAI-based extraction logic and schemas.
- `src/utils`: Cross-cutting helpers for validation and formatting.
- `app`: Streamlit application UI components.

## Non-Functional Considerations
- Environment-driven configuration loaded via `config.settings`.
- Caching and retry strategies to be implemented within tool modules.
- Logging and cost tracking to be added around API interactions.
