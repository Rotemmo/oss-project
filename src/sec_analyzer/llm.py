# src/sec_analyzer/llm.py
from __future__ import annotations
from typing import List, Dict, Optional
import os, json

# אם אין לך שרת LLM – הכלי יעבוד עם --no-llm וידלג על הקובץ הזה.
# לכן מותר להשאיר את הבקאנדים למטה "שקטים" במקרה שאין שרת זמין.

try:
    import requests  # נדרש רק אם תריצי LLM מקומי (Ollama/llama.cpp)
except Exception:  # משאיר את המודול שמיש גם בלי requests
    requests = None  # type: ignore

# מודל ברירת מחדל (כשנרצה LLM)
DEFAULT_MODEL = os.getenv("LLM_MODEL", "phi4")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OPENAI_BASE = os.getenv("OPENAI_BASE_URL", None)   # למשל: http://localhost:8080
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "no-key-needed-for-local")

ANALYSIS_SYSTEM_PROMPT = """You are a security code auditor for C/C++.
Return STRICT JSON with:
{"findings":[{"line":int,"rule_id":str,"title":str,"severity":"LOW|MEDIUM|HIGH|CRITICAL","cwe":str|null,"detail":str,"fix_suggestion":str}]}
No prose, no markdown, JSON only.
"""

def _chunk_text(text: str, max_chars: int = 20000) -> str:
    if len(text) <= max_chars:
        return text
    head = text[: max_chars // 2]
    tail = text[-max_chars // 2 :]
    return head + "\n/* ... SNIP ... */\n" + tail

def _parse_json_loose(s: str) -> Optional[Dict]:
    """ניסיון עדין לחלץ JSON גם אם המודל מחזיר טקסט לפני/אחרי."""
    try:
        start = s.find("{")
        end = s.rfind("}")
        if start != -1 and end != -1 and end > start:
            return json.loads(s[start:end+1])
    except Exception:
        return None
    return None

def analyze_with_ollama(model: str, code: str) -> Optional[List[Dict]]:
    if requests is None:
        return None
    try:
        payload = {
            "model": model,
            "prompt": ANALYSIS_SYSTEM_PROMPT + "\n\nCODE START\n" + _chunk_text(code) + "\nCODE END",
            "stream": False,
            "options": {"temperature": 0.2}
        }
        resp = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
        if resp.status_code == 200:
            txt = resp.json().get("response", "")
            j = _parse_json_loose(txt) or {}
            findings = j.get("findings", [])
            return findings if isinstance(findings, list) else []
    except Exception:
        return None
    return None

def analyze_with_openai_compat(model: str, code: str) -> Optional[List[Dict]]:
    if requests is None or not OPENAI_BASE:
        return None
    try:
        url = f"{OPENAI_BASE}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user", "content": _chunk_text(code)},
            ],
            "temperature": 0.2
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        if resp.status_code == 200:
            content = resp.json()["choices"][0]["message"]["content"]
            j = _parse_json_loose(content) or {}
            findings = j.get("findings", [])
            return findings if isinstance(findings, list) else []
    except Exception:
        return None
    return None

def analyze_code_with_llm(code: str, model: Optional[str] = None) -> List[Dict]:
    """
    מחזירה רשימת ממצאים מה־LLM אם יש שרת מקומי; אחרת [].
    שימי לב: כשמריצים את ה־CLI עם --no-llm, ה־cli בכלל לא ייכנס לפה.
    """
    model = model or DEFAULT_MODEL
    out = analyze_with_ollama(model, code)
    if isinstance(out, list):
        return out
    out = analyze_with_openai_compat(model, code)
    if isinstance(out, list):
        return out
    return []
