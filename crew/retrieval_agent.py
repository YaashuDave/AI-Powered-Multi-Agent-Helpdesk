# crew/retrieval_agent.py
# Retrieval agent: calls sqlite and web search tools and forwards results

import utils.crewai_patch_disable_llm
import utils.ollama_patch

from crewai import Agent
from a2a.a2a_protocol import send_message, BUS
from tools.sqlite_tool import sqlite_lookup
from tools.web_search import web_search
import yaml
from utils.json_parser import safe_json_parse

CONFIG = yaml.safe_load(open("yaml/retrieval_agent.yaml"))

retrieval_agent = Agent(
    name=CONFIG["name"],
    role=CONFIG["role"],
    goal=CONFIG["goal"],
    backstory=CONFIG["backstory"],
    tools=[sqlite_lookup, web_search],
    verbose=True
)


def retrieval_loop():
    BUS.register("retrieval_agent")
    while True:
        msg = BUS.receive("retrieval_agent", timeout=1)
        if not msg:
            continue

        try:
            ticket_id = msg.payload["ticket_id"]
            triage_raw = msg.payload.get("triage")
            triage = triage_raw if isinstance(triage_raw, dict) else safe_json_parse(triage_raw)

            # robust summary extraction
            summary = triage.get("summary") if isinstance(triage, dict) else None
            if not summary:
                summary = triage.get("raw_response", "") if isinstance(triage, dict) else ""

            # call tools (they return dicts)
            kb = sqlite_lookup.run(summary)
            web = web_search.run(summary)

            send_message(
                sender="retrieval_agent",
                receiver="knowledge_agent",
                type="retrieval_ready",
                payload={
                    "ticket_id": ticket_id,
                    "kb_hits": kb.get("hits", []),
                    "web_snippets": web.get("snippets", [])
                }
            )
        except Exception as e:
            send_message(
                sender="retrieval_agent",
                receiver="monitor_agent",
                type="agent_error",
                payload={"agent": "retrieval_agent", "error": str(e), "ticket_id": msg.payload.get("ticket_id")}
            )
