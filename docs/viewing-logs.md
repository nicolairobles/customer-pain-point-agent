# Viewing Application Logs

This guide explains how to view logs and debug information from the Customer Pain Point Discovery Agent.

## Quick Start

### 1. View Logs in Terminal

Logs are automatically displayed in the terminal where you run Streamlit. To see more detailed logs:

```bash
# Set log level to DEBUG for more verbose output
export LOG_LEVEL=DEBUG

# Enable agent verbose mode (shows LangChain agent reasoning steps)
export AGENT_VERBOSE=true

# Run the app
source .venv/bin/activate
streamlit run app/streamlit_app.py
```

### 2. View Debug Panel in UI

After running a query, expand the **"🔍 Debug & Logs"** panel at the bottom of the results to see:
- Execution metadata (tools used, execution time, API costs)
- Error details (if any occurred)
- Instructions for viewing terminal logs

## Log Levels

Set the `LOG_LEVEL` environment variable to control verbosity:

- `INFO` (default): Shows tool invocations, agent steps, and important events
- `DEBUG`: Shows detailed debugging information including all internal operations
- `WARNING`: Shows only warnings and errors
- `ERROR`: Shows only errors

## What Gets Logged

The application logs:

1. **Tool Invocations**: When tools (Reddit, Twitter, Google Search) are called
   - Tool name
   - Input parameters (sanitized, no credentials)
   - Output type

2. **Agent Execution**: 
   - Query start/completion
   - Tools used during execution
   - LangChain agent reasoning steps (if `AGENT_VERBOSE=true`)

3. **Errors**: 
   - Import errors
   - API failures
   - Validation errors
   - Full stack traces (in DEBUG mode)

## Example Log Output

With `LOG_LEVEL=INFO` and `AGENT_VERBOSE=true`:

```
2025-12-03 23:30:15 | src.agent.orchestrator | INFO | Using langchain version=1.1.0
2025-12-03 23:30:16 | __main__ | INFO | Agent query started: customer onboarding friction in SaaS
2025-12-03 23:30:17 | src.agent.orchestrator | INFO | tool_start name=reddit_search input=str(len=45 preview='customer onboarding friction in SaaS')
2025-12-03 23:30:20 | src.agent.orchestrator | INFO | tool_end output_type=list
2025-12-03 23:30:25 | __main__ | INFO | Agent query completed. Tools used: ['reddit_search']
```

## Troubleshooting

### No logs appearing?

1. Check that you're looking at the correct terminal (where `streamlit run` was executed)
2. Verify `LOG_LEVEL` is set correctly: `echo $LOG_LEVEL`
3. Ensure logging is configured: logs should appear even without setting `LOG_LEVEL` (defaults to INFO)

### Want to save logs to a file?

Redirect Streamlit output to a file:

```bash
streamlit run app/streamlit_app.py 2>&1 | tee app.log
```

### Need to filter logs?

Use `grep` to filter logs in the terminal:

```bash
# Show only tool invocations
streamlit run app/streamlit_app.py 2>&1 | grep "tool_start\|tool_end"

# Show only errors
streamlit run app/streamlit_app.py 2>&1 | grep -i error
```

## Security Note

Logs are sanitized to prevent credential leakage:
- API keys are never logged
- Tool inputs are summarized (not full content)
- Sensitive data is masked in log output

