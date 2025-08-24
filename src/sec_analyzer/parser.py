from typing import Tuple, Optional
from pathlib import Path

def read_file(path: str, encoding: Optional[str] = None) -> Tuple[str, Path]:
    p = Path(path).expanduser().resolve()
    if encoding:
        return p.read_text(encoding=encoding, errors="ignore"), p
    try:
        return p.read_text(encoding="utf-8"), p
    except UnicodeDecodeError:
        return p.read_text(encoding="cp1255", errors="ignore"), p

