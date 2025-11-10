# GitHub Copilot Prompt: Customer Pain Point Discovery Agent

## Project Setup Instructions

I'm building a **Customer Pain Point Discovery Agent** - an AI-powered tool that discovers customer pain points from multiple online sources (Reddit, Twitter, Google Search) and presents structured findings through a Streamlit dashboard.

### Technology Stack
- **Primary Framework**: LangChain (for agent orchestration)
- **LLM**: OpenAI GPT (for pain point extraction and categorization)
- **UI**: Streamlit
- **Language**: Python 3.10+
- **APIs**: Reddit API, Twitter API, Google Search API
- **Deployment**: Streamlit Cloud

### Project Structure

Please create the following folder structure and initial files:

```
customer-pain-point-agent/
├── .gitignore
├── README.md
├── requirements.txt
├── .env.example
├── config/
│   ├── __init__.py
│   └── settings.py
├── src/
│   ├── __init__.py
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── pain_point_agent.py
│   │   └── orchestrator.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── reddit_tool.py
│   │   ├── twitter_tool.py
│   │   └── google_search_tool.py
│   ├── extractors/
│   │   ├── __init__.py
│   │   └── pain_point_extractor.py
│   └── utils/
│       ├── __init__.py
│       ├── validators.py
│       └── formatters.py
├── app/
│   ├── __init__.py
│   ├── streamlit_app.py
│   └── components/
│       ├── __init__.py
│       ├── query_input.py
│       └── results_display.py
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_tools.py
│   └── test_extractors.py
└── docs/
    ├── setup.md
    ├── api_setup.md
    └── architecture.md
```

### Core Requirements

**Functional Requirements:**
1. Accept natural language queries (1-50 words) about customer pain points
2. Search 3 data sources: Reddit, Twitter, Google Search (5-10 results each)
3. Extract and categorize pain points using LLM with structured JSON output
4. Each pain point should include: name, description, frequency, example quote, source citation
5. Display results in intuitive Streamlit dashboard with source URLs and timestamps
6. Response time < 2 minutes per query
7. Error handling for API failures and rate limits

**Non-Functional Requirements:**
- Modular architecture (easy to add new data sources)
- Comprehensive docstrings for all functions
- Environment-based configuration (no hardcoded API keys)
- Mobile-responsive UI design
- Graceful degradation if APIs fail
- Budget constraint: OpenAI costs < $15, total < $20

### Initial File Scaffolding Needed

**requirements.txt** should include:
- langchain
- openai
- streamlit
- praw (Reddit)
- tweepy (Twitter)
- google-api-python-client
- python-dotenv
- pytest
- pydantic

**.env.example** should have placeholders for:
- OPENAI_API_KEY
- REDDIT_CLIENT_ID
- REDDIT_CLIENT_SECRET
- TWITTER_API_KEY
- TWITTER_API_SECRET
- GOOGLE_SEARCH_API_KEY
- GOOGLE_SEARCH_ENGINE_ID

**config/settings.py** should:
- Load environment variables
- Define configuration constants (max results per source, timeout limits, etc.)
- Include budget tracking variables

**src/agent/pain_point_agent.py** should:
- Implement main LangChain agent
- Use ReAct or Plan-and-Execute agent pattern
- Coordinate multiple tools (Reddit, Twitter, Google)
- Return structured JSON with pain points

**src/tools/** (reddit_tool.py, twitter_tool.py, google_search_tool.py) should:
- Implement LangChain Tool interface
- Handle API authentication
- Return 5-10 relevant results per query
- Include error handling for rate limits
- Add source metadata (URL, timestamp, author)

**src/extractors/pain_point_extractor.py** should:
- Use OpenAI to extract pain points from raw results
- Implement structured output using Pydantic models
- Categorize and de-duplicate pain points
- Calculate frequency/sentiment scores

**app/streamlit_app.py** should:
- Clean, intuitive UI with text input box
- Display results as expandable sections or data table
- Show source citations with clickable links
- Include loading spinner during API calls
- Display error messages gracefully
- Add mobile-responsive CSS

**tests/** should include:
- Unit tests for each tool
- Integration tests for agent orchestration
- Mock API responses for testing
- Test queries covering edge cases

### Architecture Notes

- Use LangChain's `AgentExecutor` for orchestration
- Implement tools as `BaseTool` subclasses
- Use Pydantic models for pain point schema validation
- Implement caching to reduce API costs
- Add retry logic with exponential backoff for API calls
- Log all API calls for debugging and cost tracking

### Output Format (JSON Schema)

```python
{
  "query": "string",
  "pain_points": [
    {
      "name": "string",
      "description": "string",
      "frequency": "high|medium|low",
      "examples": ["quote1", "quote2"],
      "sources": [
        {
          "platform": "reddit|twitter|google",
          "url": "string",
          "timestamp": "ISO8601",
          "author": "string"
        }
      ]
    }
  ],
  "metadata": {
    "total_sources_searched": "int",
    "execution_time": "float",
    "api_costs": "float"
  }
}
```

### Getting Started

Please generate:
1. Complete folder structure with all files
2. Basic scaffolding for each Python file with docstrings
3. requirements.txt with all dependencies
4. .gitignore appropriate for Python/Streamlit projects
5. .env.example with all required API keys
6. README.md with setup instructions and project overview

Focus on modularity and clean separation of concerns. Each component should be independently testable and easy to extend.

---

**Now, please create the initial repository structure with scaffolded files, focusing on the agent orchestration, tool implementations, and Streamlit UI components.**
