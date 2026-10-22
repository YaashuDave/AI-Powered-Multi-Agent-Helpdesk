import json

from a2a.a2a_protocol import A2AMessage
from validation import langgraph_agent
from validation.langgraph_agent import apply_rules


def check(result, check_id):
    return next(c for c in result["checks"] if c["id"] == check_id)


def troubleshoot_msg(steps, ticket_id="T1"):
    result = {"success": True, "notes": "", "executed_steps": steps}
    return A2AMessage(sender="t", receiver="v", type="troubleshoot_done",
                      payload={"ticket_id": ticket_id, "result": json.dumps(result)})


def test_valid_troubleshoot_passes():
    result = apply_rules(troubleshoot_msg(["a", "b", "c"]))
    assert result["passed"]
    assert check(result, "max_steps")["note"] == "3 steps (threshold 8)"


def test_too_many_steps_fails():
    result = apply_rules(troubleshoot_msg([f"step {i}" for i in range(9)]))
    assert not result["passed"]
    assert not check(result, "max_steps")["ok"]


def test_missing_ticket_id_fails():
    result = apply_rules(troubleshoot_msg(["a"], ticket_id=None))
    assert not result["passed"]


def test_uncertain_wording_is_flagged_but_advisory():
    msg = A2AMessage(sender="t", receiver="v", type="adk_context",
                     payload={"ticket_id": "T1", "enriched_context": "It could be the VPN"})
    result = apply_rules(msg)
    assert not check(result, "no_hallucination_keywords")["ok"]
    assert result["passed"]


def test_llm_hallucination_fails(monkeypatch):
    monkeypatch.setattr(langgraph_agent.ollama, "run",
                        lambda prompt: '```json\n{"hallucination": true, "uncertain_claims": ["x"]}\n```')
    result = apply_rules(troubleshoot_msg(["a"]))
    assert not result["passed"]
    assert not check(result, "llm_validation")["ok"]


def test_llm_error_does_not_crash(monkeypatch):
    def boom(prompt):
        raise ConnectionError("ollama down")

    monkeypatch.setattr(langgraph_agent.ollama, "run", boom)
    result = apply_rules(troubleshoot_msg(["a"]))
    assert "LLM error" in check(result, "llm_validation")["note"]["summary"]
