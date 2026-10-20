# crew/triage_agent.py
# Triage agent: classifies incoming user queries and sends triage_result

# very important: disable CrewAI native LLM and patch Agent.run BEFORE creating Agent
import utils.crewai_patch_disable_llm
import utils.ollama_patch

from crewai import Agent
from a2a.a2a_protocol import send_message, BUS
import yaml
from utils.json_parser import safe_json_parse

CONFIG = yaml.safe_load(open("yaml/triage_agent.yaml"))

triage_agent = Agent(
    name=CONFIG["name"],
    role=CONFIG["role"],
    goal=CONFIG["goal"],
    backstory=CONFIG["backstory"],
    verbose=True
)


def triage_loop():
    BUS.register("triage_agent")
    while True:
        incoming = BUS.receive("triage_agent", timeout=1)
        if not incoming:
            continue

        try:
            user_text = incoming.payload["text"]
            ticket_id = incoming.payload["ticket_id"]

            prompt = f"""
Classify this customer query and return a JSON object with keys:
  - category
  - urgency
  - summary
  - entities

Query: {user_text}
Return only JSON.
"""

            raw = triage_agent.run(prompt)
            parsed = safe_json_parse(raw)

            send_message(
                sender="triage_agent",
                receiver="retrieval_agent",
                type="triage_result",
                payload={"ticket_id": ticket_id, "triage": parsed}
            )

            # ADK agent enriches the triage in parallel with retrieval
            send_message(
                sender="triage_agent",
                receiver="search_adk_agent",
                type="triage_enhance",
                payload={"ticket_id": ticket_id, "triage": parsed}
            )
        except Exception as e:
            # send an error to monitor or log locally
            send_message(
                sender="triage_agent",
                receiver="monitor_agent",
                type="agent_error",
                payload={"agent": "triage_agent", "error": str(e), "ticket_id": incoming.payload.get("ticket_id")}
            )
