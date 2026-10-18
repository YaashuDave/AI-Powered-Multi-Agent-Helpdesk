# utils/ollama_client.py

import requests
import os

class OllamaClient:
    def __init__(self, model=None):
        self.base = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model = model or os.getenv("OLLAMA_MODEL", "gemma:2b")

    def run(self, prompt: str) -> str:
        """
        Basic text generation using Ollama. Returns the response text only.
        """
        response = requests.post(
            f"{self.base}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "stream": False
            },
            timeout=float(os.getenv("OLLAMA_TIMEOUT", "300"))
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    # ADK agent uses this for token estimation
    def count_tokens(self, text: str) -> int:
        return len(text.split())
