# utils/ollama_patch.py

from crewai import Agent
from utils.ollama_client import OllamaClient

# model comes from OLLAMA_MODEL (default gemma:2b)
ollama = OllamaClient()

def patched_run(self, prompt: str, **kwargs):
    return ollama.run(prompt)

# Monkey-patch globally
Agent.run = patched_run
