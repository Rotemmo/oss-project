
from typing import Tuple, Optional
import pathlib

CANDIDATE_ENCODINGS = (
    "utf-8",
    "utf-8-sig",
    "utf-16",
    "utf-16-le",
    "utf-16-be",
    "cp1255", 
    "latin-1",
)

def read_file(path: str, encoding: Optional[str] = None) -> Tuple[str, pathlib.Path]:
    p = pathlib.Path(path).expanduser().resolve()
    raw = p.read_bytes()

    if encoding:
        return (raw.decode(encoding, errors="ignore"), p)

    for enc in CANDIDATE_ENCODINGS:
        try:
            return (raw.decode(enc, errors="ignore"), p)
        except Exception:
            continue

    return (raw.decode("latin-1", errors="ignore"), p)
