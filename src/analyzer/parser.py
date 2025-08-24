from pathlib import Path
from typing import Tuple, Optional

def read_file(path: str, encoding: Optional[str] = None) -> Tuple[str, Path]:
    p = Path(path).expanduser().resolve()
    enc = encoding or "utf-8"
    return (p.read_text(encoding=enc, errors="ignore"), p)
