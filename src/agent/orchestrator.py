"""Utilities for building and configuring the LangChain agent executor."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List

try:
    from langchain_core.callbacks.base import BaseCallbackHandler  # type: ignore
except Exception:  # pragma: no cover - fallback for environments without langchain
    class BaseCallbackHandler:  # type: ignore
        """Minimal shim used when langchain callbacks are unavailable."""

        pass

from config.settings import Settings


def build_agent_executor(settings: Settings) -> Any:
    """Construct an Agent executor configured with project tools and prompts.

    LangChain imports are deferred until this function is called so that the
    module can be imported in environments with incompatible LangChain
    versions (tests, static analysis, etc.). If LangChain is missing or the
    public API changed, an informative ImportError is raised.
    """

    try:
        import langchain as _langchain

        try:
            # Preferred location (langchain>=0.3)
            from langchain.agents import create_react_agent  # type: ignore
        except Exception:
            # Fallback for installations that still expose the helper via langgraph.prebuilt
            from langgraph.prebuilt import create_react_agent  # type: ignore
    except Exception as exc:  # pragma: no cover - environment specific
        raise ImportError(
            "Failed to import required classes from langchain. This can happen if the package is not "
            "installed or if the installed version is incompatible with this code. Ensure `langchain>=1.0.7,<2` "
            "is available in your environment."
        ) from exc

    # Log LangChain version for diagnostic purposes when the agent is built.
    try:
        _lc_ver = getattr(_langchain, "__version__", None)
        if _lc_ver is None:
            try:
                from importlib import metadata as _metadata

                _lc_ver = _metadata.version("langchain")
            except Exception:
                _lc_ver = "unknown"
        import logging

        logging.getLogger(__name__).info("Using langchain version=%s", _lc_ver)
    except Exception:
        # Version logging is diagnostic only.
        pass

    tools = _load_tools(settings)
    llm = _build_llm(settings)
    telemetry_handler = _TelemetryCallbackHandler()

    # We now return an _AgentRunner that orchestrates the QueryProcessor -> Agent flow
    # Pass 'tools' and 'llm' so the runner can rebuild the agent per request with dynamic prompts.
    return _AgentRunner(
        agent_graph=None,  # Deprecated in this flow
        settings=settings,
        telemetry_handler=telemetry_handler,
        tools=tools,
        llm=llm
    )


def _load_tools(settings: Settings) -> List[Any]:
    """Instantiate tool set with shared configuration."""

    return list(_iter_tools(settings))


def _iter_tools(settings: Settings) -> Iterable[Any]:
    """Yield configured LangChain tools for the agent.

    Import tool implementations here to avoid triggering their module-level
    side-effects (pydantic model construction) during test collection.
    """

    from src.tools.reddit_tool import RedditTool
    from src.tools.twitter_tool import TwitterTool
    from src.tools.google_search_tool import GoogleSearchTool

    tool_settings = getattr(settings, "tools", None)

    def is_enabled(flag: str) -> bool:
        if tool_settings is None:
            return True
        return getattr(tool_settings, flag, True)

    if is_enabled("reddit_enabled"):
        yield RedditTool.from_settings(settings)

    if is_enabled("twitter_enabled"):
        yield TwitterTool.from_settings(settings)

    if is_enabled("google_search_enabled"):
        yield GoogleSearchTool.from_settings(settings)


def _build_llm(settings: Settings) -> Any:
    """Instantiate a chat model that is compatible with LangChain tool binding."""

    try:
        from langchain_openai import ChatOpenAI  # type: ignore
    except Exception as exc:  # pragma: no cover - environment specific
        raise ImportError(
            "ChatOpenAI is not available. Install the `langchain-openai` package to enable agent execution."
        ) from exc

    llm_settings = settings.llm
    api_settings = settings.api

    return ChatOpenAI(
        api_key=api_settings.openai_api_key,
        model=llm_settings.model,
        temperature=llm_settings.temperature,
        max_tokens=llm_settings.max_output_tokens,
        timeout=llm_settings.request_timeout_seconds,
        max_retries=llm_settings.max_retry_attempts,
    )


class _AnalystFilteredTool:
    """Wrapper that filters tool results through the analyst before returning."""
    
    def __init__(self, tool: Any, analyst: Any, runner: Any) -> None:
        self._tool = tool
        self._analyst = analyst
        self._runner = runner
        # Expose tool attributes for LangChain compatibility
        self.name = getattr(tool, 'name', 'unknown_tool')
        self.description = getattr(tool, 'description', '')
        self.args_schema = getattr(tool, 'args_schema', None)
        self.callbacks = getattr(tool, 'callbacks', [])
    
    def _run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute tool and filter results through analyst."""
        # Call the original tool
        results = self._tool._run(*args, **kwargs)
        
        # Only filter if results are a list of documents
        if not isinstance(results, list) or not results:
            return results
        
        # Check if results look like documents (have dict-like structure)
        if not all(isinstance(r, dict) for r in results):
            return results
        
        # Get current query from runner
        query = getattr(self._runner, '_current_query', '')
        if not query:
            return results
        
        # Apply analyst filtering
        filtered = self._analyst.review_and_filter_results(query, results)
        return filtered
    
    async def _arun(self, *args: Any, **kwargs: Any) -> Any:
        """Async version - just call sync for now."""
        return self._run(*args, **kwargs)
    
    def __getattr__(self, name: str) -> Any:
        """Delegate other attributes to the wrapped tool."""
        return getattr(self._tool, name)


class _AgentRunner:
    """Lightweight adapter orchestrating the query processor and research agent."""

    def __init__(
        self,
        agent_graph: Any,  # Kept for signature compatibility but ignored in new flow
        settings: Settings,
        telemetry_handler: Any | None = None,
        tools: List[Any] | None = None,
        llm: Any | None = None,
    ) -> None:
        self._recursion_limit = max(1, settings.agent.max_iterations)
        self._telemetry_handler = telemetry_handler
        self._settings = settings
        self._tools = tools or []
        self._llm = llm
        self._current_query = ""  # Store current query for analyst filtering
        
        from src.agent.query_processor import QueryProcessor
        from src.agent.analyst import Analyst
        self._query_processor = QueryProcessor(settings, llm)
        self._analyst = Analyst(settings, llm)

    def invoke(self, payload: Dict[str, Any]) -> Any:
        # 1. Analyze Query
        input_query = payload.get("input", "")
        analysis = self._query_processor.analyze(input_query)
        
        # Store query for analyst filtering
        self._current_query = input_query
        
        # 2. Build Dynamic System Prompt
        context_notes = analysis.context_notes or "No special context."
        search_terms = ", ".join(analysis.search_terms)
        subreddits = ", ".join(analysis.subreddits)
        
        system_prompt = f"""You are a research assistant that finds discussions about topics users ask about.

User Query: "{analysis.refined_query}"
Search Terms Strategy: {search_terms}
Target Subreddits: {subreddits}
Context/Instructions: {context_notes}

CRITICAL RULE FOR TOOL USAGE:
- Use the provided search terms and subreddits as your primary guide.
- When using reddit_search, use the specific subreddits identified above if possible.
- If user asks about "issues with ecommerce billing" -> query="issues with ecommerce billing" (or the refined query provided).

After searching, summarize the findings. Call the search tool only ONCE."""

        # 3. Rebuild Agent with new prompt
        # We need to import here to handle potential circular imports or lazy loading if needed,
        # but primarily to ensure we use the same creation logic.
        try:
            # Preferred location (langchain>=0.3)
            from langchain.agents import create_react_agent  # type: ignore
        except Exception:
            # Fallback for installations that still expose the helper via langgraph.prebuilt
            from langgraph.prebuilt import create_react_agent  # type: ignore

        # Wrap tools with analyst filtering
        filtered_tools = self._wrap_tools_with_analyst(self._tools)
        instrumented_tools = _attach_telemetry(filtered_tools, self._telemetry_handler)
        
        try:
            agent = create_react_agent(model=self._llm, tools=instrumented_tools, prompt=system_prompt)
        except TypeError:
            agent = create_react_agent(llm=self._llm, tools=instrumented_tools, prompt=system_prompt)

        # 4. Invoke Agent
        # Pass the refined query as input to the agent so it sees the clean version
        return agent.invoke({"input": analysis.refined_query}, config={"recursion_limit": self._recursion_limit})

    def stream(self, payload: Dict[str, Any]):
        # Duplicate logic for streaming - ideally refactor common parts
        input_query = payload.get("input", "")
        analysis = self._query_processor.analyze(input_query)
        
        # Store query for analyst filtering
        self._current_query = input_query
        
        context_notes = analysis.context_notes or "No special context."
        search_terms = ", ".join(analysis.search_terms)
        subreddits = ", ".join(analysis.subreddits)
        
        system_prompt = f"""You are a research assistant that finds discussions about topics users ask about.

User Query: "{analysis.refined_query}"
Search Terms Strategy: {search_terms}
Target Subreddits: {subreddits}
Context/Instructions: {context_notes}

CRITICAL RULE FOR TOOL USAGE:
- Use the provided search terms and subreddits as your primary guide.
- When using reddit_search, use the specific subreddits identified above if possible.

After searching, summarize the findings. Call the search tool only ONCE."""

        try:
            from langchain.agents import create_react_agent  # type: ignore
        except Exception:
            from langgraph.prebuilt import create_react_agent  # type: ignore

        # Wrap tools with analyst filtering
        filtered_tools = self._wrap_tools_with_analyst(self._tools)
        instrumented_tools = _attach_telemetry(filtered_tools, self._telemetry_handler)
        
        try:
            agent = create_react_agent(model=self._llm, tools=instrumented_tools, prompt=system_prompt)
        except TypeError:
            agent = create_react_agent(llm=self._llm, tools=instrumented_tools, prompt=system_prompt)

        yield from agent.stream({"input": analysis.refined_query}, config={"recursion_limit": self._recursion_limit})

    def get_used_tools(self) -> List[str]:
        """Return a unique list of tool names observed via telemetry."""

        handler = self._telemetry_handler
        used = getattr(handler, "used_tools", None)
        if not used:
            return []
        return sorted({str(name) for name in used if name})
    
    def _wrap_tools_with_analyst(self, tools: List[Any]) -> List[Any]:
        """Wrap tools to filter their output through the analyst."""
        wrapped = []
        for tool in tools:
            wrapped_tool = _AnalystFilteredTool(tool, self._analyst, self)
            wrapped.append(wrapped_tool)
        return wrapped


def _attach_telemetry(tools: Iterable[Any], handler: Any) -> List[Any]:
    """Attach telemetry callbacks to each tool instance."""

    instrumented: List[Any] = []
    for tool in tools:
        callbacks = list(getattr(tool, "callbacks", []) or [])
        callbacks.append(handler)
        try:
            tool.callbacks = callbacks
        except Exception:
            # If assignment fails, proceed without callbacks to avoid breaking execution.
            pass
        instrumented.append(tool)
    return instrumented


class _TelemetryCallbackHandler(BaseCallbackHandler):
    """Lightweight logger for tool invocation events (non-sensitive)."""

    ignore_agent = False
    raise_error = False

    def __init__(self) -> None:
        import logging

        self._log = logging.getLogger(__name__)
        self.used_tools: set[str] = set()

    def on_tool_start(self, serialized: Dict[str, Any] | None = None, input_str: str | None = None, **kwargs: Any) -> None:
        tool_name = (serialized or {}).get("name", "<unknown>")
        summary = _summarize_input(input_str)
        self._log.info("tool_start name=%s input=%s", tool_name, summary)
        if tool_name and tool_name != "<unknown>":
            self.used_tools.add(str(tool_name))

    def on_tool_end(self, output: Any, **kwargs: Any) -> None:
        self._log.info("tool_end output_type=%s", type(output).__name__)


def _summarize_input(input_str: Any) -> str:
    """Return a minimal, non-sensitive summary of tool input."""

    if input_str is None:
        return "<none>"
    if isinstance(input_str, dict):
        return f"dict_keys={list(input_str.keys())}"
    if isinstance(input_str, str):
        preview = input_str[:80].replace("\n", " ")
        return f"str(len={len(input_str)} preview='{preview}')"
    return f"type={type(input_str).__name__}"
