# adk_agents/search_agent.py
import os
import yaml
import threading
from adk_agents.agent_base import ADKKernel, ADKAgent
from a2a.a2a_protocol import BUS, send_message

# load yaml config
CFG = yaml.safe_load(open("adk_agents/search_agent.yaml", "r"))

MODEL = os.getenv("OLLAMA_MODEL") or CFG.get("ollama_model") or "gemma:2b"
LISTEN_TYPE = CFG.get("listen_message_type", "triage_enhance")
TARGET_RECEIVER = CFG.get("target_receiver", "knowledge_agent")
AGENT_NAME = CFG.get("name", "search_adk_agent")
DESCRIPTION = CFG.get("description", "ADK semantic enrichment")

# create kernel + agent
kernel = ADKKernel(model=MODEL)
search_adk_agent = ADKAgent(name=AGENT_NAME, description=DESCRIPTION, kernel=kernel)

# helper to run loop in background thread
def start_search_adk_loop_in_thread():
    t = threading.Thread(target=search_adk_agent.run_loop,
                         kwargs={"listen_channel": AGENT_NAME, "target_receiver": TARGET_RECEIVER, "message_type": LISTEN_TYPE},
                         daemon=True)
    t.start()
    return t

# small convenience function to run once (non-loop) for testing
def run_once(prompt_text: str) -> str:
    return search_adk_agent.run(prompt_text)
