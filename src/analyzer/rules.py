
from dataclasses import dataclass
from typing import List, Optional
import re, pathlib

@dataclass
class Finding:
    file: str
    line: int
    col: int
    rule_id: str
    title: str
    severity: str
    cwe: Optional[str]
    detail: str
    code_line: str
    fix_suggestion: str

DANGEROUS_FUNCS = {
    "gets": ("CWE-242", "Use of Inherently Dangerous Function", "Use 'fgets' with a bounded buffer and newline stripping."),
    "strcpy": ("CWE-120", "Unsafe string copy", "Use 'strncpy' or 'strlcpy' with proper bounds and explicit NUL termination."),
    "strcat": ("CWE-120", "Unsafe string concat", "Use 'strncat', 'strlcat', or 'snprintf' with proper bounds."),
    "sprintf": ("CWE-785", "sprintf without bounds", "Use 'snprintf' and limit the output length."),
    "vsprintf": ("CWE-785", "vsprintf without bounds", "Use 'vsnprintf' with a max length."),
    "scanf": ("CWE-20", "scanf without width specifier", "Add width limits like '%9s' and check return value."),
    "system": ("CWE-78", "Command injection risk", "Avoid 'system'; prefer exec* with argv or dedicated APIs; sanitize inputs."),
}

FREE_RE = re.compile(r"\bfree\s*\(\s*([a-zA-Z_][\w]*)\s*\)\s*;")
FMT_NO_FMT_RE = re.compile(r"\bprintf\s*\(\s*[^\"].*")
SCANF_UNBOUNDED_RE = re.compile(r"\bscanf\s*\(\s*\"%s\"")

def scan_lines(path: pathlib.Path) -> List[Finding]:
    findings: List[Finding] = []
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return findings

    lines = text.splitlines()
    freed_vars = set()
    for i, raw in enumerate(lines, start=1):
        line = raw.strip()

        for func, (cwe, title, fix) in DANGEROUS_FUNCS.items():
            if re.search(rf"\b{func}\s*\(", line):
                findings.append(Finding(
                    file=str(path), line=i, col=max(1, raw.find(func)+1), rule_id=f"BAN_{func.upper()}",
                    title=title, severity="HIGH" if func in {"gets","sprintf","vsprintf"} else "MEDIUM",
                    cwe=cwe, detail=f"Call to '{func}' detected which is considered unsafe.",
                    code_line=raw.rstrip(), fix_suggestion=fix
                ))

        if FMT_NO_FMT_RE.search(line):
            findings.append(Finding(
                file=str(path), line=i, col=1, rule_id="FMT_STRING_PRINTF",
                title="Possible format string vulnerability", severity="HIGH",
                cwe="CWE-134", detail="printf called without a constant format string; if input is user-controlled this is exploitable.",
                code_line=raw.rstrip(), fix_suggestion='Always use a constant format string: printf("%s", user_input);'
            ))

        if SCANF_UNBOUNDED_RE.search(line):
            findings.append(Finding(
                file=str(path), line=i, col=1, rule_id="SCANF_NO_WIDTH",
                title="Unbounded scanf %s", severity="MEDIUM",
                cwe="CWE-120", detail="Using %s without width allows buffer overflow.",
                code_line=raw.rstrip(), fix_suggestion='Add width: scanf("%63s", buf); and check return value.'
            ))

        m = FREE_RE.search(line)
        if m:
            freed_vars.add(m.group(1))

        for var in list(freed_vars):
            if re.search(rf"\b{re.escape(var)}\s*(?:->|\[|\.)", line):
                findings.append(Finding(
                    file=str(path), line=i, col=1, rule_id="UAF_HEURISTIC",
                    title="Possible use-after-free", severity="HIGH",
                    cwe="CWE-416", detail=f"Pointer '{var}' appears used after being freed earlier.",
                    code_line=raw.rstrip(), fix_suggestion=f"Set '{var}=NULL' immediately after free and avoid further use; redesign ownership."
                ))
    return findings
