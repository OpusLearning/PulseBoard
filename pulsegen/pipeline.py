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
from .exports import export_bundle
from .today import generate_today
from .visuals import ensure_visual_briefs, generate_story_images, generate_composite_image


def run(*, day: str, pulse_in: str | Path, out_dir: str | Path, voice: str = "witty-cheeky-sharp", seed: int = 0, use_ai: bool = False, use_tts: bool = False, use_cards: bool = False, use_export: bool = False, use_today: bool = False, use_images: bool = False) -> dict[str, Any]:
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

    # today.json (single payload for Today view)
    if use_today:
        import json as _json
        ap = (data_dir / "audio.json")
        cp = (data_dir / "cards.json")
        audio_obj = _json.loads(ap.read_text("utf-8")) if ap.exists() else None
        cards_obj = _json.loads(cp.read_text("utf-8")) if cp.exists() else None
        today = generate_today(pulse=pulse, editor=editor, audio=audio_obj, cards=cards_obj, day=day, use_ai=use_ai, ai=ai)
        write_json_atomic(data_dir / "today.json", today)
        paths["today_json"] = str(data_dir / "today.json")

        if use_images:
            # Enrich with visual briefs + generate images (idempotent per-day)
            today = ensure_visual_briefs(today, ai_text=ai)
            today = generate_story_images(today, out_dir=out_dir, day=day)
            today = generate_composite_image(today, out_dir=out_dir, day=day)
            write_json_atomic(data_dir / "today.json", today)
            paths["story_images"] = str(out_dir / "assets" / "story")
            paths["composite_image"] = str(out_dir / "assets" / "composite")

    if use_export:
        zp = export_bundle(out_dir=out_dir, day=day)
        paths["export_zip"] = str(zp)

    return {"ok": True, "paths": paths}
