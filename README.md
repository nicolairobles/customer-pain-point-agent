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
- Python 3.10+
- Access credentials for Reddit, Twitter, Google Search APIs, and OpenAI

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

## Project Structure
Refer to `docs/architecture.md` for detailed architectural guidance.
