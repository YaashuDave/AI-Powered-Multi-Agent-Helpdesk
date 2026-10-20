# crew/escalation_agent.py
# Escalation agent: decide whether to escalate and forward final decision

import utils.crewai_patch_disable_llm
import utils.ollama_patch

from crewai import Agent
from a2a.a2a_protocol import send_message, BUS
import yaml
from utils.json_parser import safe_json_parse

CONFIG = yaml.safe_load(open("yaml/escalation_agent.yaml"))

escalation_agent = Agent(
    name=CONFIG["name"],
    role=CONFIG["role"],
    goal=CONFIG["goal"],
    backstory=CONFIG["backstory"],
    verbose=True
)


def escalation_loop():
    BUS.register("escalation_agent")
    while True:
        msg = BUS.receive("escalation_agent", timeout=1)
        if not msg:
            continue

        try:
            ticket_id = msg.payload.get("ticket_id")
            result_raw = msg.payload.get("result")

            result = result_raw if isinstance(result_raw, dict) else safe_json_parse(result_raw)

            prompt = (
                "You are an escalation manager. Given the troubleshooting result below, "
                "decide if it needs human escalation. Return JSON with keys: escalate (true/false), reason (string).\n\n"
                f"Troubleshoot result: {result}"
            )

            raw_decision = escalation_agent.run(prompt)
            decision = safe_json_parse(raw_decision)

            send_message(
                sender="escalation_agent",
                receiver="monitor_agent",
                type="final_decision",
                payload={
                    "ticket_id": ticket_id,
                    "troubleshoot": result,
                    "escalation": decision
                }
            )
        except Exception as e:
            send_message(
                sender="escalation_agent",
                receiver="monitor_agent",
                type="agent_error",
                payload={"agent": "escalation_agent", "error": str(e), "ticket_id": msg.payload.get("ticket_id")}
            )
