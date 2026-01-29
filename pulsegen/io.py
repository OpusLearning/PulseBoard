from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def read_json(path: str | Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_atomic(path: str | Path, data: Any) -> None:
    """Write JSON atomically to avoid partially-written files on crash."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fd, tmp = tempfile.mkstemp(prefix=path.name + ".tmp.", dir=str(path.parent))
    # mkstemp defaults to 0o600; ensure public artefacts are readable after atomic replace
    try:
        mode = path.stat().st_mode & 0o777
    except FileNotFoundError:
        mode = 0o644

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            try:
                os.fchmod(fd, mode)
            except Exception:
                pass
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except OSError:
            pass
