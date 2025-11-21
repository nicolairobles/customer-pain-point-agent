### 2.05 Create WBS (Work Breakdown Structure)
```
DELIVERABLES

0.0 PROJECT MANAGEMENT
├── 1.1 Project Planning
├── 1.2 Team Coordination
├── 1.3 Status Reporting
└── 1.4 Risk Management

1.0 PHASE 1: FOUNDATION
├── 1.1 Development Environment Setup
├── 1.2 Reddit Integration
├── 1.3 LangChain Agent Core
└── 1.4 Basic Streamlit UI

2.0 PHASE 2: MULTI-SOURCE INTEGRATION
├── 2.1 Twitter/X API Integration
├── 2.2 Google Search API Integration
├── 2.3 Multi-Tool Agent Orchestration
└── 2.4 Enhanced UI (filters, export)

3.0 PHASE 3: ENHANCEMENT & POLISH
├── 3.1 Error Handling & Retry Logic
├── 3.2 Performance Optimization
├── 3.3 UI/UX Improvements
└── 3.4 Comprehensive Testing

4.0 PHASE 4: DEPLOYMENT & DOCUMENTATION
├── 4.1 Production Deployment
├── 4.2 Documentation
├── 4.3 Demo Video Creation
└── 4.4 Team Knowledge Transfer
```

**ACTIVITY LIST (Week 1 - Detailed)**

PHASE 1: FOUNDATION

```
Activity ID: 1.1.1
Activity: Create GitHub Repository
Description: Initialize repo with folder structure, README template, .gitignore
Work Package: 2.1.1 GitHub Repository Creation
Duration: 0.5 hours
Owner: Nicolai
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.1.1-create-github-repository.md)

```
Activity ID: 1.1.2
Activity: Set up Python virtual environment
Description: Create venv, install dependencies from requirements.txt
Work Package: 2.1.2 Python Environment Configuration
Duration: 0.5 hours
Story Points: 3
Owner: All team members (parallel)
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.1.2-set-up-python-virtual-environment.md)

```
Activity ID: 1.1.3
Activity: Obtain OpenAI API key
Description: Sign up, generate API key, test with simple prompt
Work Package: 2.1.3 API Key Provisioning
Story Points: 1
Duration: 0.25 hours
Owner: Nicolai
AC:
- in .env file, private
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.1.3-obtain-openai-api-key.md)

```
Activity ID: 1.1.4
Activity: Obtain Reddit API credentials
Description: Create Reddit app, get client_id and client_secret
Work Package: 2.1.3 API Key Provisioning
Duration: 0.25 hours
Story Points: 1
Owner: Nicolai
AC:
- in .env
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.1.4-obtain-reddit-api-credentials.md)

```
Activity ID: 1.1.5
Activity: Test API connections
Description: Run test scripts to verify OpenAI and Reddit APIs working
Work Package: 2.1.4 Dependency Installation
Duration: 0.5 hours
Owner: Javier, Stefan, Edison
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.1.5-test-api-connections.md)

```
Activity ID: 1.2.1
Activity: Design Reddit API wrapper interface
Description: Define function signatures and return data structure
Work Package: 2.2.1 Reddit API Wrapper Development
Duration: 1 hour
Story points: 3
Owner: Stefan
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.2.1-design-reddit-api-wrapper-interface.md) / docs/stories/1.2.1-design-reddit-api-wrapper-interface.md

```
Activity ID: 1.2.2
Activity: Implement Reddit search functionality
Description: Code search_subreddits() function with error handling
Work Package: 2.2.2 Reddit Search Functionality
Duration: 4 hours
Story Points: 5
Owner: Edison
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.2.2-implement-reddit-search-functionality.md)

```
Activity ID: 1.2.3
Activity: Implement Reddit data parsing
Description: Parse Reddit API response into standardized format
Work Package: 2.2.3 Data Parsing & Formatting
Duration: 2 hours
Story Points: 3
Owner: Javier
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.2.3-implement-reddit-data-parsing.md)

```
Activity ID: 1.2.4
Activity: Write unit tests for Reddit tool
Description: Test cases for search, parsing, error conditions
Work Package: 2.2.4 Unit Tests for Reddit Tool
Duration: 2 hours
Story Points: 3
Owner: Amanda
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.2.4-write-unit-tests-for-reddit-tool.md)

```
Activity ID: 1.3.0
Activity: Set up Open AI LLM integration point
Description: For LLM prompt interactions
Work Package: 2.3.0 LLM Integration Backbone
Story Points: 3
Duration: 1 hour
Owner: Javier
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.3.0-set-up-openai-llm-integration-point.md)

```
Activity ID: 1.3.1
Activity: Design pain point extraction prompt
Description: Write LLM prompt for extracting pain points from text
Work Package: 2.3.4 Pain Point Extraction with LLM
Story Points: 
Duration: 1 hour
Owner: Javier
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.3.1-design-pain-point-extraction-prompt.md)

---- TO CONTINUE LATER


```
Activity ID: 1.3.2
Activity: Implement pain point extractor
Description: Create extract_pain_points() function using OpenAI API
Work Package: 2.3.4 Pain Point Extraction with LLM
Story Points: 
Duration: 3 hours
Owner: Javier
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.3.2-implement-pain-point-extractor.md)

```
Activity ID: 1.3.3
Activity: Initialize LangChain agent
Description: Set up agent with ChatOpenAI and tool list
Work Package: 2.3.1 Agent Initialization
Duration: 2 hours
Owner: Stefan
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.3.3-initialize-langchain-agent.md)

```
Activity ID: 1.3.4
Activity: Register tools with agent
Description: Create Tool wrappers for Reddit search and extraction
Work Package: 2.3.2 Tool Registration
Duration: 2 hours
Owner: Stefan
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.3.4-register-tools-with-agent.md)

```
Activity ID: 1.3.5
Activity: Implement agent query processing
Description: Create run() method that orchestrates tool calls
Work Package: 2.3.3 Query Processing Logic
Duration: 3 hours
Owner: Stefan
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.3.5-implement-agent-query-processing.md)


```
Activity ID: 1.4.1
Activity: Design Streamlit UI layout
Description: Sketch UI wireframes, define components
Work Package: 2.4.1 UI Layout Design
Duration: 1 hour
Owner: Al
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.4.1-design-streamlit-ui-layout.md)

```
Activity ID: 1.4.2
Activity: Implement query input component
Description: Create text input and button in Streamlit
Work Package: 2.4.2 Query Input Component
Duration: 1 hour
Owner: Al
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.4.2-implement-query-input-component.md)

```
Activity ID: 1.4.3
Activity: Implement results display component
Description: Format and display agent output in Streamlit
Work Package: 2.4.3 Results Display Component
Duration: 2 hours
Owner: Al
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.4.3-implement-results-display-component.md)

```
Activity ID: 1.4.4
Activity: Add basic styling
Description: Apply colors, fonts, layout improvements
Work Package: 2.4.4 Basic Styling
Duration: 1 hour
Owner: Al
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.4.4-add-basic-styling.md)

```
Activity ID: 1.5.1
Activity: End-to-end testing
Description: Test complete flow from query to results
Work Package: 2.4 (Deliverable acceptance)
Duration: 1 hour
Owner: Amanda
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.5.1-end-to-end-testing.md)

```
Activity ID: 1.5.2
Activity: Code review
Description: Review all code for quality and documentation
Work Package: 2.4 (Deliverable acceptance)
Duration: 2 hours
Owner: Nicolai
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.5.2-code-review.md)

```
Activity ID: 1.5.3
Activity: Push to GitHub
Description: Commit all code with descriptive messages
Work Package: 2.4 (Deliverable acceptance)
Duration: 0.5 hours
Owner: Nicolai
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/1.5.3-push-to-github.md)

```
Activity ID: 2.1.1
Activity: Design Twitter API wrapper interface
Description: Define signatures, configuration, and schema for Twitter integration
Work Package: 3.1.1 Twitter Wrapper Design
Duration: 1 hour
Story Points: 3
Owner: Stefan
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.1.1-design-twitter-api-wrapper-interface.md)

```
Activity ID: 2.1.2
Activity: Implement Twitter search functionality
Description: Build Twitter tool that queries tweets with filters and logging
Work Package: 3.1.2 Twitter Search Implementation
Duration: 4 hours
Story Points: 5
Owner: Edison
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.1.2-implement-twitter-search-functionality.md)

```
Activity ID: 2.1.3
Activity: Implement Twitter data parsing
Description: Normalize tweet payloads into shared schema
Work Package: 3.1.3 Twitter Data Parsing
Duration: 3 hours
Story Points: 3
Owner: Javier
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.1.3-implement-twitter-data-parsing.md)

```
Activity ID: 2.1.4
Activity: Write unit tests for Twitter tool
Description: Cover success, failure, and normalization cases for Twitter integration
Work Package: 3.1.4 Twitter Tool Testing
Duration: 2 hours
Story Points: 2
Owner: Amanda
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.1.4-write-unit-tests-for-twitter-tool.md)

```
Activity ID: 2.2.1
Activity: Configure Google Custom Search
Description: Set up API credentials, environment, and smoke tests
Work Package: 3.2.1 Google Search Configuration
Duration: 1 hour
Story Points: 2
Owner: Nicolai
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.2.1-configure-google-custom-search.md)

```
Activity ID: 2.2.2
Activity: Implement Google search tool
Description: Query Custom Search API and return normalized web results
Work Package: 3.2.2 Google Search Implementation
Duration: 4 hours
Story Points: 5
Owner: Edison
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.2.2-implement-google-search-tool.md)

```
Activity ID: 2.2.3
Activity: Implement Google data parsing
Description: Clean and normalize Google result payloads
Work Package: 3.2.3 Google Data Parsing
Duration: 3 hours
Story Points: 3
Owner: Javier
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.2.3-implement-google-data-parsing.md)

```
Activity ID: 2.2.4
Activity: Write unit tests for Google tool
Description: Add regression suite for Google search integration
Work Package: 3.2.4 Google Tool Testing
Duration: 2 hours
Story Points: 2
Owner: Amanda
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.2.4-write-unit-tests-for-google-tool.md)

```
Activity ID: 2.3.1
Activity: Register new tools with agent
Description: Add Twitter and Google tools to agent configuration with guards
Work Package: 3.3.1 Agent Tool Registration
Duration: 2 hours
Story Points: 3
Owner: Stefan
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.3.1-register-new-tools-with-agent.md)

```
Activity ID: 2.3.2
Activity: Implement cross-source aggregation
Description: Merge, deduplicate, and score multi-source results
Work Package: 3.3.2 Cross-Source Aggregation
Duration: 3 hours
Story Points: 5
Owner: Javier
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.3.2-implement-cross-source-aggregation.md)

```
Activity ID: 2.3.3
Activity: Add multi-source resilience
Description: Introduce concurrency controls, timeouts, and fallbacks
Work Package: 3.3.3 Resilience & Concurrency
Duration: 3 hours
Story Points: 3
Owner: Nicolai
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.3.3-add-multi-source-resilience.md)

```
Activity ID: 2.4.1
Activity: Add source and time filters
Description: Enhance UI with filter controls and validation
Work Package: 3.4.1 Filter Enhancements
Duration: 2 hours
Story Points: 3
Owner: Al
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.4.1-add-source-and-time-filters.md)

```
Activity ID: 2.4.2
Activity: Implement results export
Description: Provide CSV/JSON export options in UI
Work Package: 3.4.2 Export Functionality
Duration: 2 hours
Story Points: 3
Owner: Al
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.4.2-implement-results-export.md)

```
Activity ID: 2.4.3
Activity: Enhance UI feedback and status messaging
Description: Add loading states, partial results banners, and cost indicators
Work Package: 3.4.3 UI Feedback Enhancements
Duration: 2 hours
Story Points: 3
Owner: Al
Story Link:
```
[Detailed Story](https://github.com/nicolairobles/customer-pain-point-agent/blob/master/docs/stories/2.4.3-enhance-ui-feedback.md)

```

