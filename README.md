# Customer Pain Point Discovery Agent

An AI-powered agent that aggregates customer pain points from Reddit, Twitter, and Google Search, extracts structured insights, and presents them in a Streamlit dashboard.

## Features
- Natural language query interface (1-50 words)
- Multi-source search across Reddit, Twitter, and Google Search
- LLM-powered pain point extraction with structured JSON output
- Streamlit dashboard for interactive exploration
- Modular architecture for adding new data sources

## Getting Started

### Prerequisites
- Python 3.11.x (project pinned to `langchain==0.0.340`; macOS users can bootstrap Miniforge and create `conda create -n cppagent-py311 python=3.11`)
- Access credentials for Reddit, Twitter, Google Search APIs, and OpenAI

### Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Environment Variables
Copy `.env.example` to `.env` and populate the required API keys.
Example entries (do not commit real keys):

```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=your_user_agent
OPENAI_API_KEY=your_openai_api_key
```

For Google Custom Search, you can follow `issues/generated/2.2.1_configure-google-custom-search.md` for setup steps. A small smoke-test script is provided at `scripts/test_google_search.py` — run it locally after setting `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID` in your `.env`.

### Running the App
```bash
streamlit run app/streamlit_app.py
```

### Testing
```bash
pytest
```

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
