from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from .io import write_json_atomic


def render_script(editor: dict[str, Any], *, max_words: int = 85) -> str:
    """Render a ~30s audio script from editor.json.

    Keep it short and punchy. Deterministic given editor input.
    """
    brief = str(editor.get("editors_brief") or "").strip()
    mm = editor.get("most_memeable") or {}
    headline = str(getattr(mm, "get", lambda k, d=None: d)("headline", "") or "").strip()

    parts = []
    if brief:
        parts.append(brief)
    if headline:
        parts.append(f"Most memeable: {headline}.")
    parts.append("That’s your Pulseboard. See you tomorrow.")

    text = " ".join(parts)

    # crude word cap
    words = text.split()
    if len(words) > max_words:
        text = " ".join(words[:max_words]).rstrip(" ,.;:") + "."

    return text


def update_audio_index(*, data_dir: Path, date_str: str, mp3_rel: str, script_rel: str, duration_s: int | None = None, max_items: int = 30) -> dict[str, Any]:
    idx_path = data_dir / "audio.json"
    items: list[dict[str, Any]] = []
    if idx_path.exists():
        import json
        items = json.loads(idx_path.read_text("utf-8")).get("items", []) or []

    # remove existing same-date
    items = [it for it in items if it.get("date") != date_str]

    items.insert(0, {
        "date": date_str,
        "mp3": mp3_rel,
        "script": script_rel,
        **({"duration_s": int(duration_s)} if duration_s is not None else {}),
    })
    items = items[:max_items]

    out = {"latest": mp3_rel, "items": items}
    write_json_atomic(idx_path, out)
    return out
