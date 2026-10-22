import os

from fastapi.testclient import TestClient

from mcp_server.mcp_server import app, run_file_parser, run_sqlite_keyword_search

client = TestClient(app)


def titles(query):
    return [hit["title"] for hit in run_sqlite_keyword_search(query)]


def test_kb_search_finds_relevant_articles():
    assert titles("User cannot log in to their account")[0] == "Login Issue"
    assert titles("VPN keeps disconnecting") == ["VPN Connection Failure"]
    assert titles("payment failed at checkout") == ["Payment Failure"]


def test_kb_search_without_matches():
    assert titles("xyz") == []
    assert titles("") == []


def test_file_parser_stays_inside_data_folder():
    assert "not allowed" in run_file_parser("../README.md")["error"]
    # an absolute path outside data/ (this test file), on any OS
    assert "not allowed" in run_file_parser(os.path.abspath(__file__))["error"]
    assert run_file_parser("missing.txt") == {"error": "File not found"}


def test_call_tool_endpoint():
    res = client.post("/call_tool", json={"tool_name": "sqlite_lookup", "payload": {"query": "printer offline"}})
    assert res.status_code == 200
    assert res.json()["hits"][0]["title"] == "Printer Not Working"

    res = client.post("/call_tool", json={"tool_name": "web_search", "payload": {"query": "vpn"}})
    assert len(res.json()["snippets"]) == 2

    res = client.post("/call_tool", json={"tool_name": "nope", "payload": {}})
    assert res.json() == {"error": "Unknown tool: nope"}
