
from typing import Tuple
import pathlib

def read_file(path: str) -> Tuple[str, pathlib.Path]:
    p = pathlib.Path(path).expanduser().resolve()
    return (p.read_text(encoding="utf-8", errors="ignore"), p)

