# Customer Pain Point Agent - Architecture Diagram (Detailed)

Below is an ASCII diagram with more technical detail, including specific libraries and architectural terms:

```
         +-------------------+
         |   Streamlit UI    |
         | (st.text_input,   |
         |  st.dataframe)    |
         +---------+---------+
                   |
                   v
         +---------+---------+
         | Agent Orchestrator|
         | (LangChain Agent  |
         |  or LangGraph)    |
         +----+----+----+----+
              |    |
     +--------+    +--------+
     |                 |
     v                 v
 +--------+       +-------------+
 |Reddit  |       | Google      |
 |API Tool|       | Search Tool |
 |(PRAW/  |       | Google API) |
 | async  |       |             |
 +---+----+       +------+------+ 
     |                 |
     +--------+--------+
           |
           v
   +--------------------------+
   | Pain Point Extractor     |
   |   (OpenAI LLM via        |
   |    LangChain/Prompt)     |
   +-----------+--------------+
               |
               v
   +--------------------------+
   | Output Formatter &       |
   | Aggregator (Pydantic,    |
   | deduplication,           |
   | citation logic)          |
   +-----------+--------------+
               |
               v
   +--------------------------+
   | Streamlit UI (Results)   |
   | (st.dataframe, st.markdown|
   +--------------------------+
```

**Key Technologies:**
- Streamlit: UI framework
- LangChain or LangGraph: Agent orchestration and tool management
- PRAW: Reddit API wrapper
- Google API: Google Search
- OpenAI LLM: Pain point extraction
- Pydantic: Data validation/structuring

**Notes:**
- The "Agent Orchestrator" is typically implemented with LangChain's Agent or LangGraph for multi-step workflows.
- Each API tool is modular and can be swapped or extended.
- Output formatting includes deduplication and citation logic before displaying results.
