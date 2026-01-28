from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json, write_json_atomic
from .editor import generate_editor
from .validate import validate_editor
from .openai_client import client_from_env


def run(*, day: str, pulse_in: str | Path, out_dir: str | Path, voice: str = "witty-cheeky-sharp", seed: int = 0, use_ai: bool = False) -> dict[str, Any]:
    out_dir = Path(out_dir)
    pulse = read_json(pulse_in)

    ai = client_from_env() if use_ai else None
    editor = generate_editor(pulse=pulse, day=day, voice=voice, seed=seed, ai=ai)
    validate_editor(editor)

    data_dir = out_dir / "data"
    write_json_atomic(data_dir / "editor.json", editor)

    return {"ok": True, "paths": {"editor": str(data_dir / "editor.json")}}
