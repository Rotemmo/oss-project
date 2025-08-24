import os
DEFAULT_MODEL = os.getenv("LLM_MODEL", "phi4")

def analyze_code_with_llm(code: str, model: str | None = None) -> list[dict]:
    # return empty list so heuristics still work
    return []