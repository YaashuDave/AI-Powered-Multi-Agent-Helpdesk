# tools/web_search.py

from crewai.tools import tool
import requests
import os

MCP_URL = os.getenv("MCP_URL", "http://localhost:8001/call_tool")

@tool("web_search")
def web_search(query: str) -> dict:
    """Performs a web search via MCP server (mocked)."""
    response = requests.post(
        MCP_URL,
        json={
            "tool_name": "web_search",
            "payload": {"query": query}
        }
    )
    response.raise_for_status()
    return response.json()
