# crew/troubleshoot_agent.py
# Troubleshoot agent: executes conceptual steps and returns results

import utils.crewai_patch_disable_llm
import utils.ollama_patch

from crewai import Agent
from a2a.a2a_protocol import send_message, BUS
import yaml
from utils.json_parser import safe_json_parse

CONFIG = yaml.safe_load(open("yaml/troubleshoot_agent.yaml"))

troubleshoot_agent = Agent(
    name=CONFIG["name"],
    role=CONFIG["role"],
    goal=CONFIG["goal"],
    backstory=CONFIG["backstory"],
    verbose=True
)


def troubleshoot_loop():
    BUS.register("troubleshoot_agent")
    while True:
        msg = BUS.receive("troubleshoot_agent", timeout=1)
        if not msg:
            continue

        try:
            ticket_id = msg.payload.get("ticket_id")
            steps_raw = msg.payload.get("steps", [])
            # steps may be dict or list or raw string
            if isinstance(steps_raw, str):
                parsed = safe_json_parse(steps_raw)
                steps = parsed if isinstance(parsed, list) else parsed.get("steps", []) if isinstance(parsed, dict) else []
            elif isinstance(steps_raw, list):
                steps = steps_raw
            elif isinstance(steps_raw, dict):
                # maybe { "0": "step1", ... } or {"steps": [...]}
                steps = steps_raw.get("steps", []) if steps_raw.get("steps") else list(steps_raw.values())
            else:
                steps = []

            prompt = (
                "Conceptually execute the following troubleshooting steps and return a JSON object:\n\n"
                f"Steps: {steps}\n\n"
                "Return JSON with keys: success (true/false), notes (string), executed_steps (array)."
            )

            raw_result = troubleshoot_agent.run(prompt)
            result = safe_json_parse(raw_result)

            send_message(
                sender="troubleshoot_agent",
                receiver="escalation_agent",
                type="troubleshoot_done",
                payload={"ticket_id": ticket_id, "result": result}
            )
        except Exception as e:
            send_message(
                sender="troubleshoot_agent",
                receiver="monitor_agent",
                type="agent_error",
                payload={"agent": "troubleshoot_agent", "error": str(e), "ticket_id": msg.payload.get("ticket_id")}
            )
