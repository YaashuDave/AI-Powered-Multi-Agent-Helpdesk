# tools/file_parser.py

from crewai.tools import tool
import requests
import os

MCP_URL = os.getenv("MCP_URL", "http://localhost:8001/call_tool")

@tool("file_parser")
def file_parser(path: str) -> dict:
    """Parses a file and extracts its raw text."""
    response = requests.post(
        MCP_URL,
        json={
            "tool_name": "file_parser",
            "payload": {"path": path}
        }
    )
    response.raise_for_status()
    return response.json()
