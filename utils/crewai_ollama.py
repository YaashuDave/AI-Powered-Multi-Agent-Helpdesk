# utils/crewai_ollama.py

from crewai.llm import LLM
from utils.ollama_client import OllamaClient

class CrewOllama(LLM):
    def __init__(self, model="gemma:2b"):
        super().__init__(model=model, provider="ollama")
        self.client = OllamaClient(model=model)

    def run(self, prompt: str, **kwargs):
        return self.client.run(prompt)
