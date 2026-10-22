# End-to-end: every agent thread, the real MCP server and the stub Ollama.
import json
import time

import fake_ollama
# imported here, before tests switch to a temp folder: the coordinator
# changes to the project root on import to load agent configs
from coordinator import coordinator


def wait_for(predicate, timeout=30):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(0.2)
    return False


def test_ticket_flows_through_all_agents(mcp_server, output_dir):
    with open(coordinator.INPUT_FILE, "w", encoding="utf-8") as f:
        f.write("I cannot log in to my account")

    coordinator.start_all_agents()
    ticket_id = coordinator.submit_ticket(coordinator.take_input())
    # the hand-off file is cleared once read
    assert coordinator.take_input() is None

    report = output_dir / "tickets" / f"{ticket_id}.json"

    def complete():
        if not report.exists():
            return False
        data = json.loads(report.read_text(encoding="utf-8"))
        return len(data["validation"]) == 3

    assert wait_for(complete), "pipeline did not finish"

    data = json.loads(report.read_text(encoding="utf-8"))
    assert data["errors"] == []
    assert data["escalation"] == {"escalate": False, "reason": "Resolved by self-service steps"}
    assert data["troubleshoot"]["success"] is True
    assert sorted(v["source_type"] for v in data["validation"]) == ["adk_context", "retrieval_ready", "troubleshoot_done"]
    assert all(v["validation"]["passed"] for v in data["validation"])

    md = (output_dir / "final.md").read_text(encoding="utf-8")
    assert ticket_id in md and "PASSED" in md

    # every LLM call asked Ollama for JSON output
    assert fake_ollama.REQUESTS and all(r.get("format") == "json" for r in fake_ollama.REQUESTS)
