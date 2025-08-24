from typing import Optional

def suggest_replacement(rule_id: str, code_line: str) -> Optional[str]:
    line = (code_line or "").strip()
    try:
        if rule_id == "BAN_GETS" and "gets(" in line:
            return line.replace("gets(", "fgets(").rstrip(");") + ", sizeof(buf), stdin);"
        if rule_id == "BAN_SPRINTF" and "sprintf(" in line:
            return line.replace("sprintf(", "snprintf(").replace(");", ", sizeof(dst));")
        if rule_id == "FMT_STRING_PRINTF" and "printf(" in line and "%s" not in line:
            return line.replace("printf(", "printf(\"%s\", ").rstrip(")")+");"
        if rule_id == "SCANF_NO_WIDTH" and "scanf(" in line and "%s" in line:
            return line.replace("%s", "%63s")
    except Exception:
        return None
    return None
