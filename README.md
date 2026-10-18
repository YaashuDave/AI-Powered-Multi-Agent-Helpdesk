# 🤖 AI-Powered Multi-Agent Helpdesk System

An intelligent, multi-agent IT helpdesk system that automates support ticket resolution using **CrewAI**, **LangGraph**, an **ADK-style** enrichment agent, **MCP (Model Context Protocol)**, and **Agent-to-Agent (A2A)** communication — all orchestrated through a central coordinator and powered by local LLMs via **Ollama**.

---

## 📌 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Agent Pipeline](#agent-pipeline)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Configuration](#configuration)
- [Maintainer](#maintainer)
- [License](#license)

---

## Overview

This system receives a user's support ticket (e.g., *"I cannot log in"*), routes it through a pipeline of specialized AI agents, and produces:

- A **structured JSON report** with troubleshooting steps and escalation decisions.
- A **human-readable Markdown report** summarizing the resolution.

The agents are built on different frameworks (CrewAI, LangGraph and a lightweight ADK-style runtime), demonstrating multi-framework orchestration over a shared message bus.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                    Streamlit / CLI Interface                  │
└────────────────────────────┬─────────────────────────────────┘
                             │  User submits ticket
                             ▼
┌──────────────────────────────────────────────────────────────┐
│                      COORDINATOR                             │
│              (Starts all agents, dispatches tickets)         │
└────────────────────────────┬─────────────────────────────────┘
                             │  A2A Message Bus
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────────┐  ┌────────────────┐
│  CrewAI       │  │  ADK-style        │  │  LangGraph      │
│  Agents (5)   │  │  Search Agent     │  │  Validation     │
│               │  │                   │  │  Agent          │
│ • Triage      │  │  Enriches triage  │  │                 │
│ • Retrieval   │  │  with root cause, │  │  Rule engine +  │
│ • Knowledge   │  │  related issues & │  │  LLM-based      │
│ • Troubleshoot│  │  recommendations  │  │  hallucination  │
│ • Escalation  │  │                   │  │  detection      │
└───────┬───────┘  └────────┬──────────┘  └───────┬─────────┘
        │                   │                     │
        └───────────────────┼─────────────────────┘
                            ▼
               ┌─────────────────────┐
               │   Monitor Agent      │
               │   (Final Output)     │
               │   → final.json       │
               │   → final.md         │
               └─────────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                     MCP Tool Server                          │
│            FastAPI server exposing shared tools               │
│         (SQLite KB lookup, File parser, Web search)          │
│                  http://localhost:8001                        │
└──────────────────────────────────────────────────────────────┘
```

---

## Agent Pipeline

| #  | Agent                | Framework  | Role                                                                 |
|----|----------------------|------------|----------------------------------------------------------------------|
| 1  | **Triage Agent**     | CrewAI     | Classifies the ticket — extracts category, urgency, summary, entities |
| 2  | **Retrieval Agent**  | CrewAI     | Searches the knowledge base (SQLite) and web for relevant solutions   |
| 3  | **Knowledge Agent**  | CrewAI     | Combines KB hits, web snippets and ADK context into troubleshooting steps |
| 4  | **Troubleshoot Agent** | CrewAI   | Walks through the steps and reports success, notes and executed steps |
| 5  | **Escalation Agent** | CrewAI     | Decides whether to escalate the ticket to a human agent              |
| 6  | **Search Agent**     | ADK-style  | Enriches the triage with a root-cause guess, related issues and recommendations |
| 7  | **LangGraph Agent**  | LangGraph  | `StateGraph` that validates outputs — rule checks and LLM hallucination detection |
| 8  | **Monitor Agent**    | Custom     | Aggregates results, validations and errors into `final.json` / `final.md` |

---

## Tech Stack

| Component              | Technology                        |
|------------------------|-----------------------------------|
| **Agent Frameworks**   | CrewAI, LangGraph, ADK-style runtime |
| **LLM Runtime**        | Ollama (local) — `gemma:2b`       |
| **Inter-Agent Comms**  | Custom A2A Protocol (message bus)  |
| **Tool Server**        | MCP Server (FastAPI + Uvicorn)     |
| **Knowledge Base**     | SQLite                             |
| **Web Interface**      | Streamlit                          |
| **Configuration**      | YAML agent configs                 |
| **Data Validation**    | Pydantic                           |

---

## Project Structure

```
AI-enabled-HelpDesk/
│
├── main.py                    # CLI entry point (starts MCP + Coordinator)
├── streamlit_app.py           # Streamlit Web UI
├── monitor.py                 # Monitor agent — writes final output
├── create_db.py               # Seeds the SQLite knowledge base
├── test_runner.py             # Test runner script
├── coordinator_input.txt      # Ticket hand-off file (runtime, gitignored)
├── requirements.txt           # Python dependencies
├── .gitignore
│
├── coordinator/
│   └── coordinator.py         # Central orchestrator — starts all agents
│
├── crew/                      # CrewAI-based agents
│   ├── triage_agent.py
│   ├── retrieval_agent.py
│   ├── knowledge_agent.py
│   ├── troubleshoot_agent.py
│   └── escalation_agent.py
│
├── adk_agents/                # ADK-style agent runtime
│   ├── agent_base.py
│   ├── search_agent.py
│   └── search_agent.yaml
│
├── validation/                # LangGraph validation agent
│   └── langgraph_agent.py
│
├── a2a/                       # Agent-to-Agent communication protocol
│   └── a2a_protocol.py
│
├── mcp_server/                # MCP Tool Server (FastAPI)
│   └── mcp_server.py
│
├── tools/                     # Shared tools exposed via MCP
│   ├── sqlite_tool.py
│   ├── file_parser.py
│   └── web_search.py
│
├── utils/                     # Utility modules
│   ├── ollama_client.py
│   ├── ollama_patch.py
│   ├── crewai_ollama.py
│   ├── crewai_patch_disable_llm.py
│   └── json_parser.py
│
├── yaml/                      # YAML configurations for each agent
│   ├── triage_agent.yaml
│   ├── retrieval_agent.yaml
│   ├── knowledge_agent.yaml
│   ├── troubleshoot_agent.yaml
│   ├── escalation_agent.yaml
│   └── langgraph_agent.yaml
│
├── data/
│   └── sample_kb.sqlite       # SQLite knowledge base
│
└── output/                    # Generated at runtime (gitignored)
    ├── logs/
    │   └── run.log
    ├── tickets/               # One report per ticket
    ├── final.json
    └── final.md
```

---

## Getting Started

### Prerequisites

- **Python 3.10 – 3.13** (tested on 3.11; CrewAI does not support 3.14 yet)
- **Ollama** installed and running locally — [Install Ollama](https://ollama.com/)
- Pull the required model:
  ```bash
  ollama pull gemma:2b
  ```

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/YaashuDave/AI-enabled-HelpDesk.git
   cd AI-enabled-HelpDesk
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**

   - **Windows (PowerShell)**
     ```powershell
     .\.venv\Scripts\Activate
     ```
   - **macOS / Linux**
     ```bash
     source .venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Seed the knowledge base** (optional — a seeded `data/sample_kb.sqlite` is included)
   ```bash
   python create_db.py
   ```

---

## Usage

### Option 1 — Streamlit Web UI (Recommended)

```bash
streamlit run streamlit_app.py
```

Opens a browser at `http://localhost:8501` with:
- A text area to submit support tickets
- Live system logs
- Final Markdown and JSON output panels

### Option 2 — CLI Mode

```bash
python main.py
```

This starts both the MCP server and the coordinator, then presents an interactive CLI:

```
=== AI Multi-Agent Helpdesk (CLI Mode) ===
Type your issue below. Type 'exit' to quit.

Enter issue: I cannot log in to my account
✔ Issue submitted: "I cannot log in to my account"
Agents processing...
```

---

## How It Works

1. **User submits a ticket** via Streamlit UI or CLI, which write it to `coordinator_input.txt`.
2. **Coordinator** picks up the ticket and dispatches it to the **Triage Agent** over the A2A message bus.
3. **Triage Agent** (CrewAI) classifies the issue → sends `triage_result` to the **Retrieval Agent** and `triage_enhance` to the **Search Agent**.
4. **Retrieval Agent** (CrewAI) queries the SQLite KB and web search via the **MCP Server** → sends `retrieval_ready`.
5. **Search Agent** (ADK-style) runs in parallel and adds a root-cause guess, related issues and recommendations → sends `adk_context`.
6. **Knowledge Agent** (CrewAI) waits for both inputs and turns them into troubleshooting steps → sends `steps_ready`.
7. **Troubleshoot Agent** (CrewAI) walks through the steps → sends `troubleshoot_done`.
8. **Escalation Agent** (CrewAI) decides whether the issue needs human intervention → sends `final_decision`.
9. **LangGraph Validation Agent** subscribes to `retrieval_ready`, `adk_context` and `troubleshoot_done` and runs each through a `StateGraph` (rule checks → LLM hallucination check → decision).
10. **Monitor Agent** merges the decision, validations and any agent errors into `output/final.json`, `output/final.md` and `output/tickets/<ticket_id>.*`. If an agent fails, the ticket is reported and marked for escalation.

> **Note:** CrewAI is used for the agent definitions (role, goal, backstory); each agent's LLM call is routed straight to Ollama (`utils/ollama_patch.py`). The Search Agent is a small ADK-style runtime written for this project, not the `google-adk` package. Web search is mocked.

---

## Configuration

All agent configurations are stored in `yaml/` as YAML files. Each file defines:

- `name` — Agent identifier
- `role` — Description of the agent's role
- `goal` — What the agent aims to achieve
- `backstory` — Context for the LLM persona
- `tools` — List of MCP tools the agent can use

The LangGraph agent has additional configuration for validation rules and message routing.

Environment variables:

| Variable           | Default                    | Purpose                                    |
|--------------------|----------------------------|--------------------------------------------|
| `OLLAMA_URL`       | `http://localhost:11434`   | Ollama server                              |
| `OLLAMA_MODEL`     | `gemma:2b`                 | Model used by every agent                  |
| `OLLAMA_TIMEOUT`   | `300`                      | Seconds to wait for one LLM response       |
| `MCP_URL`          | `http://localhost:8001/call_tool` | Tool server endpoint used by agents |
| `MCP_HOST` / `MCP_PORT` | `127.0.0.1` / `8001`  | Tool server bind address                   |
| `ADK_WAIT_SECONDS` | `120`                      | How long the Knowledge Agent waits for ADK context |

---

## Maintainer

**Yaashu Dave**

---

## Key Protocols

### A2A (Agent-to-Agent) Protocol

A thread-safe in-process message bus (`a2a/a2a_protocol.py`) enabling structured communication between agents using **Pydantic** message envelopes. Agents can also `subscribe` to message types to receive a copy (used by the validation agent):

```python
class A2AMessage(BaseModel):
    sender: str
    receiver: str
    type: str
    payload: Dict[str, Any]
    timestamp: str
```

### MCP (Model Context Protocol) Server

A **FastAPI** server (`mcp_server/mcp_server.py`) that exposes shared tools:

| Tool             | Description                                  |
|------------------|----------------------------------------------|
| `sqlite_lookup`  | Ranked keyword search over KB titles and content |
| `file_parser`    | Reads files inside `data/` (first 3000 chars) |
| `web_search`     | Web search (mock — can be replaced with a live API) |

---

## License

This project is for educational and demonstration purposes.
