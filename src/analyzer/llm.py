from __future__ import annotations
from typing import List, Dict, Optional
import os, requests, json, re, sys

# --------- Config ---------
DEFAULT_MODEL = os.getenv("LLM_MODEL", "phi4")
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")
OPENAI_BASE  = os.getenv("OPENAI_BASE_URL", None)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "no-key-needed-for-local")
DEBUG = os.getenv("LLM_DEBUG", "0") == "1"

def _dbg(msg: str):
    if DEBUG:
        print(f"[LLM] {msg}", file=sys.stderr)

# --------- Prompt ---------
ANALYSIS_SYSTEM_PROMPT = """\
You are a security code auditor for C/C++. Task: find vulnerabilities and propose minimal, safe fixes.
Return ONLY a JSON object with this schema (no prose/markdown/fences):

{
  "findings": [
    {
      "line": 1,
      "rule_id": "LLM_FINDING",
      "title": "Short title",
      "severity": "LOW|MEDIUM|HIGH|CRITICAL",
      "cwe": "CWE-###",
      "detail": "One or two concise sentences.",
      "fix_suggestion": "Minimal safe fix."
    }
  ]
}
"""

# --------- Helpers ---------
def _chunk_text(text: str, max_chars: int = 20000) -> str:
    if len(text) <= max_chars:
        return text
    half = max_chars // 2
    return text[:half] + "\n/* ... SNIP ... */\n" + text[-half:]

def _strip_fences(t: str) -> str:
    return re.sub(r"```(?:json)?\s*([\s\S]*?)```", r"\1", t, flags=re.IGNORECASE).strip()

def _try_parse_findings(txt: str) -> Optional[List[Dict]]:
    if not txt:
        return None
    t = _strip_fences(txt)

    # 1) כולו JSON
    try:
        j = json.loads(t)
        if isinstance(j, dict) and "findings" in j:
            return j["findings"]
    except Exception:
        pass

    # 2) לאתר בלוק JSON ראשון בטקסט
    s, e = t.find("{"), t.rfind("}")
    if s != -1 and e != -1 and e > s:
        blob = t[s:e+1]
        try:
            j = json.loads(blob)
            if isinstance(j, dict) and "findings" in j:
                return j["findings"]
        except Exception as ex:
            _dbg(f"JSON slice parse failed: {ex}")

    # 3) לפעמים מוחזר מערך בלבד
    if t.lstrip().startswith("["):
        try:
            arr = json.loads(t)
            if isinstance(arr, list):
                return arr
        except Exception:
            pass

    return None

def _fallback_raw(txt: str, source: str) -> List[Dict]]:
    """החזרה פשוטה: Finding יחיד עם הטקסט הגולמי כדי שתראה שה-LLM רץ."""
    return [{
        "line": 1,
        "rule_id": "LLM_FINDING",
        "title": f"LLM Analysis ({source})",
        "severity": "INFO",
        "cwe": None,
        "detail": (txt or "").strip(),
        "fix_suggestion": ""
    }]

# --------- Backends ---------
def _ollama_generate(model: str, code: str) -> List[Dict]:
    try:
        payload = {
            "model": model,
            "prompt": ANALYSIS_SYSTEM_PROMPT + "\n\nCODE START\n" + _chunk_text(code) + "\nCODE END",
            "stream": False,
            "options": {"temperature": 0.2},
        }
        _dbg(f"POST {OLLAMA_URL}/api/generate model={model}")
        r = requests.post(f"{OLLAMA_URL}/api/generate", json=payload, timeout=120)
        _dbg(f"status={r.status_code}")
        if r.status_code == 200:
            txt = r.json().get("response", "")
            findings = _try_parse_findings(txt)
            if findings:
                return findings
            _dbg("no JSON parsed; returning fallback (generate)")
            return _fallback_raw(txt, "generate")
    except Exception as e:
        _dbg(f"ollama generate failed: {e}")
    return []

def _ollama_chat(model: str, code: str) -> List[Dict]:
    try:
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user",   "content": _chunk_text(code)},
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
        _dbg(f"POST {OLLAMA_URL}/api/chat model={model}")
        r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=120)
        _dbg(f"status={r.status_code}")
        if r.status_code == 200:
            data = r.json()
            txt = data.get("message", {}).get("content", "")
            findings = _try_parse_findings(txt)
            if findings:
                return findings
            _dbg("no JSON parsed; returning fallback (chat)")
            return _fallback_raw(txt, "chat")
    except Exception as e:
        _dbg(f"ollama chat failed: {e}")
    return []

def _openai_compat(model: str, code: str) -> List[Dict]:
    if not OPENAI_BASE:
        return []
    try:
        url = f"{OPENAI_BASE}/v1/chat/completions"
        headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                {"role": "user",   "content": _chunk_text(code)},
            ],
            "temperature": 0.2,
        }
        _dbg(f"POST {url} model={model}")
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        _dbg(f"status={r.status_code}")
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"]
            findings = _try_parse_findings(content)
            if findings:
                return findings
            _dbg("no JSON parsed; returning fallback (openai-compat)")
            return _fallback_raw(content, "openai-compat")
    except Exception as e:
        _dbg(f"openai-compat failed: {e}")
    return []

# --------- Public API ---------
def analyze_code_with_llm(code: str, model: Optional[str] = None) -> List[Dict]:
    model = model or DEFAULT_MODEL
    # סדר נסיון: generate -> chat -> openai-compat
    out = _ollama_generate(model, code)
    if out: return out
    out = _ollama_chat(model, code)
    if out: return out
    out = _openai_compat(model, code)
    if out: return out
    _dbg("LLM returned nothing")
    return []
