import sys, os
# logs contain emoji/arrows; Windows pipes default to cp1252
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT)
# agent configs are loaded with relative paths
os.chdir(ROOT)

import threading
import time
from datetime import datetime

# === A2A BUS ===
from a2a.a2a_protocol import BUS, send_message, A2AMessage

# === CrewAI Agent Loops ===
from crew.triage_agent import triage_loop
from crew.retrieval_agent import retrieval_loop
from crew.knowledge_agent import knowledge_loop
from crew.troubleshoot_agent import troubleshoot_loop
from crew.escalation_agent import escalation_loop

# === ADK Agent Loop ===
from adk_agents.search_agent import start_search_adk_loop_in_thread

# === LangGraph Agent Loop ===
from validation.langgraph_agent import start_langgraph_loop_in_thread

# === Monitor Agent ===
# Monitor writes final.json, final.md and logs
from monitor import monitor_loop


# ========== DIRECTORY SETUP ==========
os.makedirs("output", exist_ok=True)
os.makedirs("output/logs", exist_ok=True)

LOG_FILE = "output/logs/run.log"
INPUT_FILE = "coordinator_input.txt"

def log(msg: str):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")



# ========== THREAD STARTER ==========
def start_thread(target, name):
    t = threading.Thread(target=target, daemon=True)
    t.name = name
    t.start()
    log(f"Started thread: {name}")
    return t



# ========== COORDINATOR START ==========
def start_all_agents():
    log("Starting Multi-Agent System...")

    # CREW AGENTS
    start_thread(triage_loop, "triage_agent")
    start_thread(retrieval_loop, "retrieval_agent")
    start_thread(knowledge_loop, "knowledge_agent")
    start_thread(troubleshoot_loop, "troubleshoot_agent")
    start_thread(escalation_loop, "escalation_agent")

    # ADK AGENT
    start_search_adk_loop_in_thread()
    log("Started ADK search agent")

    # LANGGRAPH AGENT
    start_langgraph_loop_in_thread()
    log("Started LangGraph validation agent")

    # MONITOR AGENT
    start_thread(monitor_loop, "monitor_agent")

    log("All agents started successfully.")
    log("System ready to accept tickets.\n")



# ========== ISSUE A NEW TICKET ==========
def submit_ticket(text: str):
    ticket_id = f"TKT-{int(time.time() * 1000)}"
    log(f"Submitting ticket {ticket_id}: {text}")

    send_message(
        sender="coordinator",
        receiver="triage_agent",
        type="new_ticket",
        payload={"ticket_id": ticket_id, "text": text}
    )

    return ticket_id



# ========== INPUT WATCHER ==========
def take_input():
    """Return the pending ticket text from INPUT_FILE and clear it."""
    if not os.path.exists(INPUT_FILE):
        return None
    with open(INPUT_FILE, "r+", encoding="utf-8") as f:
        text = f.read().strip()
        f.seek(0)
        f.truncate()
    return text or None


# ========== MAIN RUNNER ==========
def run():
    take_input()   # drop anything left over from a previous run
    start_all_agents()
    log(f"Watching {INPUT_FILE} for new tickets (written by main.py / streamlit_app.py).")

    # Monitor writes final.json/final.md for each ticket
    while True:
        text = take_input()
        if text:
            submit_ticket(text)
        time.sleep(0.5)



if __name__ == "__main__":
    run()
