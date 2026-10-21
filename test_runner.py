from validation.langgraph_agent import start_langgraph_loop_in_thread
from a2a.a2a_protocol import BUS, send_message
import time

print("Starting LangGraph agent loop...")
start_langgraph_loop_in_thread()

BUS.register("monitor_agent")

print("LangGraph agent started. Sending message...")

send_message(
    "tester",
    "langgraph_agent",
    "retrieval_ready",
    {
        "ticket_id": "TKT-LG-1",
        "kb_hits": [{"title": "Login Issue", "content": "reset password steps..."}],
        "web_snippets": ["snippet about reset password"]
    }
)

print("Message sent. Waiting for validation...")

msg = BUS.receive("monitor_agent", timeout=10)
print("MONITOR RECEIVED:", msg)
