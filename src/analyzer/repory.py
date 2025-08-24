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
    runs = [{"tool":{"driver":{"name":"llm-sec-analyzer"}},"results":[]}]
    for f in findings:
        level = "error" if (f.get("severity","").upper() in ("HIGH","CRITICAL")) else ("warning" if f.get("severity","").upper()=="MEDIUM" else "note")
        runs[0]["results"].append({
            "ruleId": f.get("rule_id","GENERIC"),
            "level": level,
            "message": {"text": f"{f['title']}: {f['detail']} Fix: {f.get('fix_suggestion','')}"},
            "locations": [{
                "physicalLocation": {
                    "artifactLocation": {"uri": str(f.get("file","?"))},
                    "region": {"startLine": f["line"]}
                }
            }]
        })
    return json.dumps({"version":"2.1.0","$schema":"https://json.schemastore.org/sarif-2.1.0.json","runs":runs}, indent=2)
