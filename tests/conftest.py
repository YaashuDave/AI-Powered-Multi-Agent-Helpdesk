# tests/conftest.py
# Runs everything offline: a stub Ollama and the real MCP server on free ports.
# Env vars must be set before agent modules are imported, since clients read
# them at import time.
import os
import socket
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tests"))
os.chdir(ROOT)   # agent configs are loaded with relative paths

import fake_ollama  # noqa: E402

_ollama = fake_ollama.start()
os.environ["OLLAMA_URL"] = f"http://127.0.0.1:{_ollama.server_address[1]}"


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


MCP_PORT = _free_port()
os.environ["MCP_URL"] = f"http://127.0.0.1:{MCP_PORT}/call_tool"

import pytest  # noqa: E402


@pytest.fixture(scope="session")
def mcp_server():
    import uvicorn
    from mcp_server.mcp_server import app

    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=MCP_PORT, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.05)
    yield os.environ["MCP_URL"]
    server.should_exit = True


@pytest.fixture
def output_dir(tmp_path, monkeypatch):
    """Run in a temp folder with the output/ layout the monitor writes to."""
    for d in ("output/logs", "output/tickets"):
        (tmp_path / d).mkdir(parents=True)
    monkeypatch.chdir(tmp_path)
    return tmp_path / "output"
