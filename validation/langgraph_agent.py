# validation/langgraph_agent.py
# Validation agent built as a LangGraph StateGraph:
#   rule_checks -> llm_validation -> decide
import yaml
import threading
from typing import Dict, Any, List, TypedDict

from langgraph.graph import StateGraph, START, END

from a2a.a2a_protocol import BUS, send_message, A2AMessage
from utils.ollama_client import OllamaClient
from utils.json_parser import safe_json_parse

CFG = yaml.safe_load(open("yaml/langgraph_agent.yaml", "r"))

AGENT_NAME = CFG.get("name", "langgraph_agent")
TARGET_RECEIVER = CFG.get("target_receiver", "monitor_agent")
LISTEN_TYPES = set(CFG.get("listen_message_types", []))
RULES = CFG.get("rules", [])
UNCERTAIN_TOKENS = ["maybe", "could be", "might be", "not sure", "possibly"]

ollama = OllamaClient()


class ValidationState(TypedDict):
    message_type: str
    payload: Dict[str, Any]
    text: str
    checks: List[Dict[str, Any]]
    passed: bool


def _parse(value):
    parsed = safe_json_parse(value) if value else {}
    return {} if isinstance(parsed, dict) and "raw_response" in parsed else parsed


def _evidence_text(message_type: str, payload: Dict[str, Any]) -> str:
    if message_type == "retrieval_ready":
        kb = " ".join(str(x.get("content", "")) for x in (payload.get("kb_hits") or []))
        return kb + " " + " ".join(payload.get("web_snippets") or [])
    if message_type == "adk_context":
        return str(payload.get("enriched_context") or "")
    if message_type == "troubleshoot_done":
        return str(payload.get("result") or "")
    return str(payload)


# ---------- graph nodes ----------
def rule_checks(state: ValidationState) -> Dict[str, Any]:
    payload = state["payload"]
    checks = []

    # Rule: must have ticket_id
    ticket_id = payload.get("ticket_id")
    checks.append({"id": "must_have_ticket_id", "ok": bool(ticket_id),
                   "note": None if ticket_id else "Missing ticket_id"})

    # Rule: troubleshoot step count limit
    if state["message_type"] == "troubleshoot_done":
        parsed = _parse(payload.get("result"))
        steps = (parsed.get("executed_steps") or parsed.get("steps") or []) if isinstance(parsed, dict) else []
        cnt = len(steps) if isinstance(steps, list) else 0
        threshold = next((r["threshold"] for r in RULES if r["id"] == "max_steps"), 8)
        checks.append({"id": "max_steps", "ok": cnt <= threshold,
                       "note": f"{cnt} steps (threshold {threshold})"})

    # Rule: no uncertain wording presented as fact
    found = [t for t in UNCERTAIN_TOKENS if t in state["text"].lower()]
    checks.append({"id": "no_hallucination_keywords", "ok": not found,
                   "note": f"uncertain wording: {found}" if found else None})

    return {"checks": checks}


def llm_validation(state: ValidationState) -> Dict[str, Any]:
    prompt = (
        "You are a validation assistant. Inspect the following text and answer in JSON:\n\n"
        f"TEXT: {state['text']}\n\n"
        "Return JSON with keys: { 'hallucination': true/false, 'uncertain_claims': [ ... ], 'summary': 'short' }\n"
        "Hallucination = claims that cannot be substantiated by KB or are nonsensical.\n"
    )
    try:
        llm_resp = ollama.run(prompt)
        parsed = safe_json_parse(llm_resp)
        if not isinstance(parsed, dict) or "raw_response" in parsed:
            parsed = {"hallucination": False, "uncertain_claims": [], "summary": llm_resp[:300]}
    except Exception as e:
        parsed = {"hallucination": False, "uncertain_claims": [], "summary": f"LLM error: {e}"}

    check = {"id": "llm_validation", "ok": not parsed.get("hallucination", False), "note": parsed}
    return {"checks": state["checks"] + [check]}


def decide(state: ValidationState) -> Dict[str, Any]:
    # wording checks are advisory; these rules decide pass/fail
    hard = {"must_have_ticket_id", "max_steps", "llm_validation"}
    return {"passed": all(c["ok"] for c in state["checks"] if c["id"] in hard)}


def build_graph():
    graph = StateGraph(ValidationState)
    graph.add_node("rule_checks", rule_checks)
    graph.add_node("llm_validation", llm_validation)
    graph.add_node("decide", decide)
    graph.add_edge(START, "rule_checks")
    graph.add_edge("rule_checks", "llm_validation")
    graph.add_edge("llm_validation", "decide")
    graph.add_edge("decide", END)
    return graph.compile()


GRAPH = build_graph()


def apply_rules(message: A2AMessage) -> Dict[str, Any]:
    payload = message.payload or {}
    state = GRAPH.invoke({
        "message_type": message.type,
        "payload": payload,
        "text": _evidence_text(message.type, payload),
        "checks": [],
        "passed": True,
    })
    return {"passed": state["passed"], "checks": state["checks"]}


def langgraph_loop():
    # receive a copy of every pipeline message we validate
    BUS.subscribe(AGENT_NAME, LISTEN_TYPES)
    while True:
        msg = BUS.receive(AGENT_NAME, timeout=1)
        if not msg:
            continue
        # only handle defined types
        if msg.type not in LISTEN_TYPES:
            continue
        try:
            outcome = apply_rules(msg)
            decision = {
                "ticket_id": msg.payload.get("ticket_id"),
                "source_type": msg.type,
                "validation": outcome
            }
            send_message(sender=AGENT_NAME, receiver=TARGET_RECEIVER, type=CFG.get("send_message_type", "validation_result"), payload=decision)
        except Exception as exc:
            send_message(sender=AGENT_NAME, receiver=TARGET_RECEIVER, type="validation_error", payload={"ticket_id": msg.payload.get("ticket_id"), "error": str(exc)})


# helper to start loop in background thread
def start_langgraph_loop_in_thread():
    t = threading.Thread(target=langgraph_loop, daemon=True)
    t.start()
    return t
