# adk_agents/agent_base.py
"""
Small ADK-style runtime (local, lightweight) for the project.
Provides:
 - ADKKernel: wraps OllamaClient to provide run() for prompts
 - ADKAgent: small agent class that exposes .run(prompt) and a run_loop that listens on A2A
This is intentionally minimal and self-contained (no external google packages).
"""

from typing import Any, Dict
from utils.ollama_client import OllamaClient
import threading
import time
from a2a.a2a_protocol import BUS, send_message

class ADKKernel:
    """Thin wrapper over OllamaClient to match ADK-like API."""
    def __init__(self, model: str = None):
        self.client = OllamaClient(model=model)

    def run(self, prompt: str, max_tokens: int = 512) -> str:
        # OllamaClient has .run or .generate depending on your utils file.
        # We call .run if present, else .generate, else .chat fallback.
        if hasattr(self.client, "run"):
            return self.client.run(prompt)
        if hasattr(self.client, "generate"):
            data = self.client.generate(prompt, max_tokens=max_tokens)
            # try to extract sensible text from returned object
            if isinstance(data, dict):
                # Ollama local output shapes vary; use best-effort
                return data.get("response") or data.get("text") or str(data)
            return str(data)
        if hasattr(self.client, "chat"):
            return self.client.chat([{"role":"user","content":prompt}], max_tokens=max_tokens)
        raise RuntimeError("Ollama client has no run/generate/chat method")


class ADKAgent:
    """Minimal ADK-style agent. Accepts a name, description, kernel, and a simple run() wrapper."""
    def __init__(self, name: str, description: str, kernel: ADKKernel):
        self.name = name
        self.description = description
        self.kernel = kernel
        self._stop = False

    def run(self, prompt: str) -> str:
        return self.kernel.run(prompt)

    def stop(self):
        self._stop = True

    def run_loop(self, listen_channel: str, target_receiver: str, message_type: str):
        """
        Simple loop: registers on A2A BUS at listen_channel, and for each message,
        processes and sends enriched result to target_receiver.
        message_type is the 'type' this ADK agent will respond to (e.g. 'triage_enhance')
        """
        BUS.register(self.name)
        while not self._stop:
            msg = BUS.receive(self.name, timeout=1)
            if not msg:
                time.sleep(0.1)
                continue
            try:
                # Only process matching message types
                if msg.type != message_type:
                    continue

                # Expect payload has 'triage' and 'ticket_id'
                triage = msg.payload.get("triage")
                ticket_id = msg.payload.get("ticket_id")

                prompt = (
                    "You are an ADK semantic enrichment agent.\n\n"
                    "Input TRIAGE summary (raw):\n"
                    f"{triage}\n\n"
                    "Task: produce a JSON object with keys: "
                    "'root_cause_guess', 'related_issues', 'missing_info', 'recommendations'.\n"
                    "Return only JSON.\n"
                )

                enriched_text = self.run(prompt)

                # send enriched text as payload to target_receiver
                send_message(
                    sender=self.name,
                    receiver=target_receiver,
                    type="adk_context",
                    payload={"ticket_id": ticket_id, "enriched_context": enriched_text}
                )
            except Exception as e:
                # On error, send an error payload so pipeline can monitor
                send_message(
                    sender=self.name,
                    receiver=target_receiver,
                    type="adk_context_error",
                    payload={"ticket_id": msg.payload.get("ticket_id"), "error": str(e)}
                )
