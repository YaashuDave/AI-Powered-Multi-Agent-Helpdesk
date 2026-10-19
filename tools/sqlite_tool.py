# tools/sqlite_tool.py

from crewai.tools import tool
import requests
import os

MCP_URL = os.getenv("MCP_URL", "http://localhost:8001/call_tool")

@tool("sqlite_lookup")
def sqlite_lookup(query: str) -> dict:
    """Searches the local SQLite knowledge base for relevant information."""
    response = requests.post(
        MCP_URL,
        json={
            "tool_name": "sqlite_lookup",
            "payload": {"query": query}
        }
    )
    response.raise_for_status()
    return response.json()
