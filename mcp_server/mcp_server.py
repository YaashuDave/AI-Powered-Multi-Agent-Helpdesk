# mcp_server/mcp_server.py
"""
Real MCP-style Tool Server using FastAPI.
Agents (CrewAI / ADK / LangGraph) will call these tools through HTTP.
"""

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
import sys
import os
import re
import sqlite3
from pathlib import Path

app = FastAPI(title="MCP Tool Server", version="1.0")

# Path to the SQLite KB created in Step 1
DATA_FOLDER = Path(__file__).resolve().parent.parent / "data"
DB_FILE = DATA_FOLDER / "sample_kb.sqlite"


# ------------------------------
# Generic ToolCall Input Model
# ------------------------------
class ToolCall(BaseModel):
    tool_name: str
    payload: Dict[str, Any]


# ------------------------------
# SQLite KB Lookup Tool
# ------------------------------
STOPWORDS = {
    "the", "a", "an", "to", "is", "am", "are", "i", "my", "me", "not", "cannot",
    "can't", "unable", "able", "and", "or", "of", "in", "on", "for", "with",
    "user", "issue", "problem", "it", "this", "that", "when", "trying", "get",
}


def keywords(query: str):
    words = re.findall(r"[a-z0-9]+", query.lower())
    # crude stemming so "logging"/"logged" still match "login"
    stems = {w[:5] if len(w) > 5 else w for w in words if w not in STOPWORDS and len(w) > 2}
    return sorted(stems)


def run_sqlite_keyword_search(query: str):
    terms = keywords(query)
    if not terms:
        return []

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT title, content FROM kb")
    rows = cursor.fetchall()
    conn.close()

    scored = []
    for title, content in rows:
        text = f"{title} {content}".lower()
        score = sum(1 for t in terms if t in text)
        # title matches count double
        score += sum(1 for t in terms if t in title.lower())
        if score:
            scored.append((score, title, content))

    scored.sort(key=lambda r: r[0], reverse=True)
    # drop weak matches on a single common word
    best = scored[0][0] if scored else 0
    return [{"title": t, "content": c} for score, t, c in scored[:5] if score * 2 >= best]


# ------------------------------
# File Parser Tool
# ------------------------------
def run_file_parser(path: str):
    # only files inside data/ can be read
    path = (DATA_FOLDER / path).resolve()
    if not path.is_relative_to(DATA_FOLDER):
        return {"error": "Access outside the data folder is not allowed"}
    if not path.is_file():
        return {"error": "File not found"}

    text = path.read_text(encoding="utf-8")
    return {"text": text[:3000]}  # limit output for safety


# ------------------------------
# Web Search Tool (Mock for Now)
# ------------------------------
def run_web_search(query: str):
    return {
        "snippets": [
            f"Mock snippet for '{query}' - replace with live search later.",
            f"Search result about '{query}' from simulated engine."
        ]
    }


# ------------------------------
# MCP Tool Dispatcher Endpoint
# ------------------------------
@app.post("/call_tool")
async def call_tool(request: ToolCall):
    """Dispatch incoming tool calls to the correct handler."""
    tool = request.tool_name
    payload = request.payload

    if tool == "sqlite_lookup":
        q = payload.get("query", "")
        return {"hits": run_sqlite_keyword_search(q)}

    elif tool == "file_parser":
        path = payload.get("path", "")
        return run_file_parser(path)

    elif tool == "web_search":
        q = payload.get("query", "")
        return run_web_search(q)

    else:
        return {"error": f"Unknown tool: {tool}"}


# ------------------------------
# MCP SERVER ENTRY POINT
# ------------------------------
if __name__ == "__main__":
    # Windows pipes default to cp1252, which cannot print emoji
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    host = os.getenv("MCP_HOST", "127.0.0.1")
    port = int(os.getenv("MCP_PORT", "8001"))
    print(f"🔥 MCP Tool Server Running on: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)
