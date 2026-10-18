# utils/crewai_patch_disable_llm.py

# 🔥 Completely disable CrewAI's native LLM loading (OpenAI, Anthropic, etc.)
# This solves: "OPENAI_API_KEY is required"

import crewai.utilities.llm_utils as llm_utils

def no_llm(*args, **kwargs):
    return None

# Override ALL LLM loaders
llm_utils.create_llm = no_llm
llm_utils._llm_via_environment_or_fallback = no_llm
