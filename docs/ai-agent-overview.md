# Single-Purpose AI Agent Project Guide (Intermediate Level)

## Project Overview: Specialized AI Research/Competitive Analysis Agent

**What You'll Build:**  
A focused AI agent that performs research or competitive analysis tasks automatically. It takes a user prompt (e.g., “Give me a competitive analysis of Company X”) and (a) queries live web data through APIs or web search, (b) summarizes relevant information, and (c) presents structured findings—optionally with citations or links.

**Examples:**
- Market research bot: Given a domain/company, crawls key sites, summarizes latest news/funding/features.
- Interview prep agent: Gathers recent press releases, Glassdoor reviews, LinkedIn employee trends, product changes, and synthesizes insights.
- Technology landscape scout: Given a tool name, summarizes top competitors, their features, and differentiators.

**Estimated Time:** 3-4 weeks
**Difficulty:** Intermediate  
**Demo-ability:** ⭐⭐⭐⭐⭐ (Shows real automation and applied LLMs)

---

## Why This Project is Great
- **Highly practical** – Directly imitates junior analyst work or PM research
- **Modern agent skills** – Demonstrates LangChain, OpenAI Functions, agent frameworks
- **Structured output** – Generates tables, competitor briefs, timelines, or action items
- **Expandable** – Start simple (one tool/task), add capabilities one at a time
- **Strong talking point** – “I built a research agent that automates…”

---

## What You'll Learn
- **Agent frameworks (LangChain Agents, AutoGPT, CrewAI)**
- **Function calling (OpenAI, LangChain Tools)**
- **Tool integration (web search, APIs, file reading, vector DBs, scraping)**
- **Prompt engineering for multi-step tasks**
- **Error handling and retry patterns**
- **Chaining tool responses and maintaining agent workflow state**
- **Evaluating autonomy vs. human-in-the-loop**

---

## System/Agent Workflow
```
User Prompt
   ↓
Agent parses task
   ↓
Select (or plan) workflow/tools needed
   ↓
Call first tool – e.g., Web search API, scrape site, call external API
   ↓
Process/parse external data
   ↓
Store intermediate results (memory)
   ↓
Repeat or trigger next tool/task
   ↓
Synthesize/summarize in LLM
   ↓
Return structured report
```

---

## Tech Stack

- **Language Model:** OpenAI API (GPT-4o-mini recommended), Anthropic, or open-source like Llama 3 (via Hugging Face)
- **Agent Frameworks:**
  - LangChain Agents (core, popular)
  - OpenAI Function Calling
  - CrewAI (experimental, designed for multi-agent)
  - AutoGPT (optional for autonomous demos)
- **Tools/Integrations:**
  - Bing Web Search API (or SerpAPI, ContextAPI) for real-time web
  - Requests, BeautifulSoup/Scrapy for custom scraping
  - YouTube, News, Twitter, LinkedIn APIs (optional)
  - Google Custom Search (free/paid)
- **Vector DB (optional for storing/skimming docs):** Pinecone, Chroma
- **Interface:** Streamlit (web dashboard), FastAPI (for API), or CLI with Rich
- **Collaboration/Version Control:** GitHub

---

## Project Phases & Timeline
### *Example: 4-Week Plan*

**Phase 1 (Week 1): Define Use Case & Minimum Workflow**
- Define agent specialty (e.g., customer pain point discovery agent)
- List must-have tools (e.g., Bing Search API, URL summarizer)
- Write simple functional spec with user stories (Product: Al)
- Set initial evaluation metric (e.g., “agent finds 3+ relevant competitor features in <2 min”)

**Phase 2 (Week 2): Build Simple Agent**
- Set up LangChain Agent and plug in OpenAI API (Nicolai: TPM & technical lead)
- Integrate first tool (web search)
- Create initial prompt/playground for task
- Code agent to reason about which tool to use for each sub-task
- Handle basic tool calling and returning results
- CLI/UI for demoing single-task run

**Phase 3 (Week 3): Add More Tools & Robustness**
- Add 1-2 more tools (YouTube summary, Glassdoor reviews, etc.)
- Implement error catching, logging, retry loops (catch failed API calls, bad output)
- Store agent “memory” (JSON, session state)
- Allow users to pick task focus (e.g., specify company or category)
- Add human-in-the-loop “pause/approve” on critical actions

**Phase 4 (Week 4): Polish and Demo**
- Build Streamlit dashboard (visual task selection, agent output as cards/tables)
- UX improvements (status/progress, iteration counter)
- Add simple evaluation/test harness
- Document usage and assumptions
- Run demo with 5–10 real tasks; collect feedback

---

## Team Roles

- Al (Product): Defines use cases, writes specs, creates evaluation tasks, shapes output for usability.
- Nicolai (Technical PM): Sets technical milestones, coordinates API/tool integrations, QA, deployment.
- Edison, Javier, Stefan (Developers): Build and debug agent, write tool wrappers, implement error handling, deploy and monitor.
- Ray (Scrum Master): Runs sprints, tracks progress, documents retrospectives, schedules check-ins.
- Amanda (QA): Stress-tests agent, writes test cases ("what if the web page is slow?"), documents bugs.

---

## Complete Tutorials & Code Resources

### Step-by-Step Guides
- **LangChain Agents Quickstart (Official):**
  https://python.langchain.com/docs/modules/agents/

- **OpenAI Function Calling Tutorial:**
  https://platform.openai.com/docs/guides/function-calling

- **CrewAI Guide & Multi-Agent Examples:**
  https://docs.crewai.com/
  https://github.com/crewAIInc/crewAI-examples

- **AutoGPT (full project repo):**
  https://github.com/Significant-Gravitas/Auto-GPT

### Finished and Working Project Links
- **Web Search Agent Starter (LangChain):**
  https://github.com/langchain-ai/langchain-examples/blob/main/agents/tools-websearch.py
- **LangChain Policy Analyst Agent (YouTube news summary):**
  https://github.com/langchain-ai/langchain-cookbook/tree/main/quickstart_policyanalyst
- **CrewAI Example Multi-Tool Agent:**
  https://github.com/crewAIInc/crewAI-examples/blob/main/examples/websearch_summarizer.py
- **Agent Web Demo (Streamlit + LangChain)**
  https://github.com/streamlit/streamlit-agent-webdemo (shows tool-using agent with dashboard)
- **Google Search + Summarize Agent:**
  https://github.com/hwchase17/langchain-google-search-agent

### Blogs & Videos
- **Video: "LangChain Agent: Build a Custom AI Tool-using Agent"**
  https://www.youtube.com/watch?v=yQI_J10LQuU
- **AutoGPT walkthrough (“Can it actually do anything?”):**
  https://www.youtube.com/watch?v=qbIk7-JPB2c
- **CrewAI Multi-Agent Guide (DataCamp):**
  https://www.datacamp.com/blog/top-ai-agent-projects

### General API for Web+News Search
- **SerpAPI (free for Google Search):**
  https://serpapi.com/
- **ContextAPI (web news search):**
  https://contextapi.dev/

---

## Demo Strategy
- *Show end-to-end run for a task*: Enter prompt, watch agent plan, call web search/API, summarize in dashboard/table
- *Visual dashboard*: Streamlit – show task status, intermediate tool calls, final report
- *Structured output*: Tables, links, competitor feature list, press releases cited
- *Test with real-world prompts and compare with manual results (for evaluation)*

---

## Bonus: Typical Agent Use Cases Your Team Can Build
- Competitive product feature summary
- Recent company news headlines and summaries
- Social sentiment round-up for a product/brand
- Interview prep digest for a company or role
- VC/funding scout: List 3-5 most recent investors or fundraises in a niche
- Tech landscape: List competitors, show pricing/positioning (as available)

---

## Evaluation Metrics
- **Coverage:** Did the agent find all core competitors or news?
- **Relevance:** Are sources timely and credible?
- **Accuracy:** Are summaries faithful to linked material?
- **Autonomy:** How far can agent run before error/human input?
- **Response time:** Is agent fast (< 2 minutes for a run)?

---

## Common Pitfalls & Fixes
- **Tool/API fails:** Always catch errors, retry, or switch tool
- **Hallucination:** Require citations/source text in final answer
- **Over-reliance on one tool:** Modularize agent so new tools can be swapped in easily
- **Timeouts:** Set sensible iteration/time limits
- **Security:** Avoid agent writing to or scraping sensitive pages without clear controls

---

## Next Steps / Week-by-Week Task List

1. Define goal + must-have use case (“competitive analysis agent”)
2. Run LangChain Agent quickstart locally with web search tool
3. Integrate one new source/tool each (news, social, API)
4. Build minimal Streamlit dashboard to display agent output
5. Implement error handling and logs
6. Polish UX, document code, test end-to-end
7. Deploy/record demo; share repo and live link
8. Prepare bullet points for interview portfolio

**You can build and extend from these working repos!**
