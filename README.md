# framework-free-agent

> Build autonomous AI agents from scratch — no black boxes, no magic, just Python.

This repository demonstrates how to implement a fully functional **ReAct (Reasoning + Acting) agent** without relying on high-level agent abstractions. It also includes a parallel implementation using **LangGraph** and a document-editing agent, making it a practical reference for understanding what agent frameworks actually do under the hood.

---

## Why Framework-Free?

Popular agent frameworks like LangChain's agent executor abstract away the control loop, memory management, tool dispatch, and reflection — which makes them powerful but opaque. This project implements each of those components explicitly, so you can see exactly how they work and why they exist.

---

## Features

- **ReAct loop** — Thought → Action → Observation cycle with full step-by-step logging
- **Reflection** — A secondary LLM call evaluates each step and the final answer, triggering a revision if needed
- **Persistent memory** — The full history of thoughts, actions, and observations is injected into every subsequent prompt
- **Tool use** — Extensible tool registry; ships with `search_wikipedia`
- **Safety guardrails** — Infinite loop detection, forced tool use before finishing, format error recovery
- **LangGraph comparison** — The same agent rebuilt with LangGraph for a side-by-side contrast
- **Document agent** — A LangGraph-powered writing assistant with `update` and `save` tools (`agent-5.py`)

---

## Repository Structure

```
framework-free-agent/
├── ReAct-Agent.py                  # Hand-rolled ReAct agent (no framework)
├── ReAct-Agent-with-LangGraph.py   # Same agent rebuilt with LangGraph
├── agent-5.py                      # "Drafter" — document update/save agent
└── LICENSE
```

---

## How the ReAct Agent Works

```
Question
   │
   ▼
build_prompt()          ← question + full memory history
   │
   ▼
LLM call                ← returns Thought / Action / Action Input
   │
   ▼
parse_response()        ← extracts structured fields from free text
   │
   ▼
execute_action()        ← runs the tool or triggers finish
   │
   ▼
reflect()               ← second LLM call: CONTINUE or REVISE?
   │
   ├─ REVISE → loop back (up to max_steps)
   └─ CONTINUE → store in memory, next step
```

The agent enforces that `search_wikipedia` is called at least once before it is allowed to return a final answer.

---

## Tech Stack

| Component | Technology |
|---|---|
| LLM | LLaMA 3.3 70B via [Groq](https://groq.com) |
| LangGraph agent | LangGraph + LangChain |
| Tool use | Custom Python functions / LangChain `@tool` |
| Environment | `python-dotenv` |

---

## Getting Started

**1. Clone the repository**

```bash
git clone https://github.com/asfandyar-prog/framework-free-agent.git
cd framework-free-agent
```

**2. Install dependencies**

```bash
pip install langchain-groq langgraph python-dotenv wikipedia
```

**3. Set your API key**

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key_here
```

**4. Run the framework-free agent**

```bash
python ReAct-Agent.py
```

**5. Run the LangGraph version**

```bash
python ReAct-Agent-with-LangGraph.py
```

**6. Run the document agent**

```bash
python agent-5.py
```

---

## Example Output

```
LLM Response:
Thought: I need to search for information about this topic.
Action: search_wikipedia
Action Input: Alan Turing

Step 1
Thought: I need to search for information about this topic.
Action: search_wikipedia
Action Input: Alan Turing
Observation: Alan Mathison Turing was an English mathematician, computer scientist...

Reflection: CONTINUE

Final Answer: Alan Turing was a British mathematician and computer scientist widely
regarded as the father of theoretical computer science and artificial intelligence...
```

---

## Project Files

### `ReAct-Agent.py`
The core of the project. A fully self-contained agent loop built with plain Python and direct LLM API calls. Demonstrates memory construction, response parsing, tool dispatch, reflection, and loop detection without any agent framework.

### `ReAct-Agent-with-LangGraph.py`
The identical agent behaviour reimplemented using LangGraph's `StateGraph`. Useful for comparing what the framework handles automatically versus what you had to write manually in the framework-free version.

### `agent-5.py`
"Drafter" — a document editing agent built on LangGraph. The LLM can call an `update` tool to modify an in-memory document and a `save` tool to write it to disk. The graph terminates automatically once the document is saved.

---

## Key Concepts Demonstrated

**ReAct pattern** — Interleaving reasoning (Thought) and acting (Action) in a loop, as described in the [ReAct paper](https://arxiv.org/abs/2210.03629).

**Reflection** — Using a second LLM call to critique the agent's own output before committing to it, improving answer quality without human intervention.

**Prompt-based memory** — No vector store or external database; the agent's entire history is serialised directly into the prompt on each step.

**Conditional graph edges** — In the LangGraph versions, `should_continue` determines whether the graph loops back to the agent node or terminates at `END`.

---

## License

MIT — see [LICENSE](LICENSE) for details.
