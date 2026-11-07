import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .config import settings


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".writing-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def digest(value: Any) -> str:
    data = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(data.encode()).hexdigest()


def active_release() -> tuple[str, Path]:
    pointer = read_json(settings.data_dir / "active.json")
    release_id = pointer["id"]
    if not release_id.startswith("mcs-") or any(
        c not in "abcdefghijklmnopqrstuvwxyz0123456789-" for c in release_id
    ):
        raise ValueError("Invalid release pointer")
    path = settings.data_dir / "releases" / release_id
    if not path.is_dir():
        raise FileNotFoundError("The active release is unavailable")
    return release_id, path
