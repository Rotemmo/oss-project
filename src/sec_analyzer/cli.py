# src/sec_analyzer/cli.py
import typer, pathlib
from typing import Optional, List, Dict
from rich import print as rprint

from .parser import read_file
from .rules import scan_lines
from .report import to_text, to_json, to_sarif
from .fixes import suggest_replacement

DEFAULT_MODEL = "phi4"  # ישתנה ל-llm.DEFAULT_MODEL אם תפעילי LLM

def _cli(
    file: str = typer.Argument(..., help="Path to C/C++ file to analyze"),
    output_format: str = typer.Option("text", "--format", case_sensitive=False, help="text|json|sarif"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM model name (when LLM enabled)"),
    apply: bool = typer.Option(False, "--apply", help="Apply trivial single-line fixes in-place when safe"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Disable LLM usage (heuristics only)"),
    encoding: Optional[str] = typer.Option(None, "--encoding", help="Source file encoding (e.g., cp1255, utf-8)"),
):
    code, path = read_file(file, encoding=encoding)

    heuristics = scan_lines(path)
    llm_findings: List[Dict] = []
    if not no_llm:
        try:
            from .llm import analyze_code_with_llm as _llm_analyze, DEFAULT_MODEL as _DM
            model = model or _DM
            llm_findings = _llm_analyze(code=code, model=model)
        except Exception:
            llm_findings = []

    all_findings: List[Dict] = []
    for f in heuristics:
        all_findings.append({
            "file": str(path), "line": f.line, "severity": f.severity, "rule_id": f.rule_id,
            "title": f.title, "detail": f.detail, "cwe": f.cwe, "code_line": f.code_line,
            "fix_suggestion": f.fix_suggestion
        })
    for f in llm_findings:
        all_findings.append({
            "file": str(path), "line": int(f.get("line", 1)), "severity": f.get("severity","MEDIUM"),
            "rule_id": f.get("rule_id","LLM_FINDING"), "title": f.get("title","Potential issue"),
            "detail": f.get("detail",""), "cwe": f.get("cwe"), "code_line": "", "fix_suggestion": f.get("fix_suggestion","")
        })
    all_findings.sort(key=lambda x: (x["file"], x["line"]))

    if apply and all_findings:
        lines = code.splitlines(keepends=True)
        changed = False
        for f in all_findings:
            rep = suggest_replacement(f.get("rule_id",""), f.get("code_line",""))
            if rep is not None and f.get("code_line"):
                idx = f["line"] - 1
                if 0 <= idx < len(lines):
                    lines[idx] = rep + ("" if lines[idx].endswith("\n") else "\n")
                    changed = True
        if changed:
            path.write_text("".join(lines), encoding=encoding or "utf-8")
            rprint(f"[green]Applied trivial fixes to {path}[/green]")

    if output_format.lower() == "json":
        print(to_json(all_findings))
    elif output_format.lower() == "sarif":
        print(to_sarif(all_findings))
    else:
        print(to_text(all_findings))

def main():
    # זה ה־entry point שמפורסם בסקריפט – הוא מריץ את ה־CLI האמיתי דרך Typer
    typer.run(_cli)
