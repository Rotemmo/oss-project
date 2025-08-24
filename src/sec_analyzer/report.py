
from typing import List, Dict
import json, pathlib

def to_text(findings: List[Dict]) -> str:
    out = []
    for f in findings:
        loc = f.get("file","?")
        out.append(f"{pathlib.Path(loc).name}:{f['line']} [{f['severity']}] {f['title']} ({f.get('rule_id','')}{' / ' + f.get('cwe','') if f.get('cwe') else ''})")
        out.append(f"    ↳ {f['detail']}")
        if f.get("fix_suggestion"):
            out.append(f"    Fix: {f['fix_suggestion']}")
    return "\n".join(out) if out else "No findings."

def to_json(findings: List[Dict]) -> str:
    return json.dumps({"findings": findings}, indent=2, ensure_ascii=False)

def to_sarif(findings: List[Dict]) -> str:
    runs = [{
        "tool": {"driver": {"name": "llm-sec-analyzer"}},
        "results": []
    }]
    for f in findings:
        runs[0]["results"].append({
            "ruleId": f.get("rule_id","GENERIC"),
            "level": severity_to_level(f.get("severity","MEDIUM")),
            "message": {"text": f"{f['title']}: {f['detail']} Fix: {f.get('fix_suggestion','')}"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": str(f.get("file","?"))},
                    "region": {"startLine": f["line"]}
                }
            }]
        })
    sarif = {"version": "2.1.0", "$schema": "https://json.schemastore.org/sarif-2.1.0.json", "runs": runs}
    return json.dumps(sarif, indent=2)

def severity_to_level(sev: str) -> str:
    sev = (sev or "").upper()
    if sev in ("CRITICAL","HIGH"):
        return "error"
    if sev == "MEDIUM":
        return "warning"
    return "note"
