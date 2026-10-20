# crew/knowledge_agent.py
# Knowledge agent: synthesize KB + web + ADK context into troubleshooting steps

import utils.crewai_patch_disable_llm
import utils.ollama_patch

from crewai import Agent
from a2a.a2a_protocol import send_message, BUS
import os
import time
import yaml
from utils.json_parser import safe_json_parse

CONFIG = yaml.safe_load(open("yaml/knowledge_agent.yaml"))

knowledge_agent = Agent(
    name=CONFIG["name"],
    role=CONFIG["role"],
    goal=CONFIG["goal"],
    backstory=CONFIG["backstory"],
    verbose=True
)


# how long to wait for ADK context once retrieval results are in
ADK_WAIT_SECONDS = float(os.getenv("ADK_WAIT_SECONDS", "120"))


def knowledge_loop():
    BUS.register("knowledge_agent")
    # ticket_id -> {"retrieval": payload, "adk": payload, "since": ts}
    pending = {}

    while True:
        msg = BUS.receive("knowledge_agent", timeout=1)
        if msg:
            entry = pending.setdefault(msg.payload.get("ticket_id"), {"since": time.time()})
            if msg.type == "retrieval_ready":
                entry["retrieval"] = msg.payload
            elif msg.type in ("adk_context", "adk_context_error"):
                entry["adk"] = msg.payload

        # synthesise once both inputs are in, or ADK is taking too long
        for ticket_id, entry in list(pending.items()):
            if "retrieval" not in entry:
                continue
            if "adk" not in entry and time.time() - entry["since"] < ADK_WAIT_SECONDS:
                continue
            del pending[ticket_id]
            synthesise(ticket_id, entry["retrieval"], entry.get("adk") or {})


def synthesise(ticket_id, retrieval, adk):
    try:
        kb_hits = retrieval.get("kb_hits", [])
        web_snippets = retrieval.get("web_snippets", [])
        # ADK enriched context may arrive as text or dict
        enriched = adk.get("enriched_context")
        enriched_parsed = enriched if isinstance(enriched, dict) else safe_json_parse(enriched) if enriched else {}

        prompt = (
            "You are a senior support analyst. Based on the following inputs, "
            "create clear step-by-step troubleshooting instructions.\n\n"
            f"KB HITS: {kb_hits}\n\nWEB SNIPPETS: {web_snippets}\n\nADK CONTEXT: {enriched_parsed}\n\n"
            "Return only JSON like: {\"steps\": [\"step1\", \"step2\", ...]}"
        )

        raw_steps = knowledge_agent.run(prompt)
        steps = safe_json_parse(raw_steps)

        send_message(
            sender="knowledge_agent",
            receiver="troubleshoot_agent",
            type="steps_ready",
            payload={"ticket_id": ticket_id, "steps": steps}
        )
    except Exception as e:
        send_message(
            sender="knowledge_agent",
            receiver="monitor_agent",
            type="agent_error",
            payload={"agent": "knowledge_agent", "error": str(e), "ticket_id": ticket_id}
        )
