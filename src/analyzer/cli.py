# למעלה:
import typer
from typing import Optional, List, Dict
from .parser import read_file
from .rules import scan_lines
from .llm import analyze_code_with_llm, DEFAULT_MODEL
from .report import to_text, to_json, to_sarif
from .fixes import suggest_replacement

def main(
    file: str = typer.Argument(..., help="Path to C/C++ file to analyze"),
    output_format: str = typer.Option("text", "--format", case_sensitive=False, help="text|json|sarif"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="LLM model (default env LLM_MODEL or 'phi4')"),
    apply: bool = typer.Option(False, "--apply", help="Apply trivial single-line fixes in-place when safe"),
    no_llm: bool = typer.Option(False, "--no-llm", help="Disable LLM usage (heuristics only)"),
    encoding: Optional[str] = typer.Option(None, "--encoding", help="Force file encoding (e.g. utf-8, cp1255, utf-16-le)"),
):
    code, path = read_file(file, encoding=encoding)
    heuristics = scan_lines(path)
    llm_findings: List[Dict] = []
    if not no_llm:
        llm_findings = analyze_code_with_llm(code=code, model=model or DEFAULT_MODEL)
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
            path.write_text("".join(lines), encoding="utf-8")
            from rich import print as rprint
            rprint(f"[green]Applied trivial fixes to {path}[/green]")
    if output_format.lower() == "json":
        print(to_json(all_findings))
    elif output_format.lower() == "sarif":
        print(to_sarif(all_findings))
    else:
        print(to_text(all_findings))

if __name__ == "__main__":
    typer.run(main)
