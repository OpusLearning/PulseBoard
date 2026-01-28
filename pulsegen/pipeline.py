from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json, write_json_atomic
from .editor import generate_editor
from .validate import validate_editor
from .openai_client import client_from_env
from .audio import render_script, update_audio_index
from .elevenlabs_client import tts_from_env
from .cards import render_cards


def run(*, day: str, pulse_in: str | Path, out_dir: str | Path, voice: str = "witty-cheeky-sharp", seed: int = 0, use_ai: bool = False, use_tts: bool = False, use_cards: bool = False) -> dict[str, Any]:
    out_dir = Path(out_dir)
    pulse = read_json(pulse_in)

    ai = client_from_env() if use_ai else None
    editor = generate_editor(pulse=pulse, day=day, voice=voice, seed=seed, ai=ai)
    validate_editor(editor)

    data_dir = out_dir / "data"
    write_json_atomic(data_dir / "editor.json", editor)

    paths = {"editor": str(data_dir / "editor.json")}

    if use_tts:
        tts = tts_from_env()
        script = render_script(editor)
        audio_dir = out_dir / "assets" / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        mp3_path = audio_dir / f"{day}.mp3"
        script_path = audio_dir / f"{day}.txt"
        mp3_bytes = tts.synth_mp3(text=script)
        mp3_path.write_bytes(mp3_bytes)
        script_path.write_text(script + "\n", encoding="utf-8")
        mp3_rel = f"assets/audio/{day}.mp3"
        script_rel = f"assets/audio/{day}.txt"
        update_audio_index(data_dir=data_dir, date_str=day, mp3_rel=mp3_rel, script_rel=script_rel)
        paths["audio_mp3"] = str(mp3_path)
        paths["audio_script"] = str(script_path)

    if use_cards:
        render_cards(editor=editor, out_dir=out_dir, day=day)
        paths["cards_json"] = str(data_dir / "cards.json")

    return {"ok": True, "paths": paths}
