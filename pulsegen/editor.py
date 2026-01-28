from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import re
import random

from .ai import AIClient


WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-']+")


def _theme_key(title: str) -> str:
    words = [w.lower() for w in WORD_RE.findall(title) if len(w) >= 5]
    if not words:
        return "misc"
    return words[0]


def generate_editor(*, pulse: dict[str, Any], day: str, voice: str, seed: int = 0, ai: AIClient | None = None) -> dict[str, Any]:
    """Generate editor.json from pulse.json.

    Deterministic given (pulse, day, voice, seed) when ai is None or deterministic.
    """
    items = list(pulse.get("items") or [])
    rng = random.Random(seed)

    # Themes (MVP heuristic)
    themes: dict[str, dict[str, Any]] = {}
    for it in items:
        title = str(it.get("title") or "")
        link = str(it.get("link") or "")
        key = _theme_key(title)
        bucket = themes.setdefault(key, {"theme": key, "count": 0, "links": []})
        bucket["count"] += 1
        if link and len(bucket["links"]) < 3:
            bucket["links"].append(link)

    top_themes = sorted(themes.values(), key=lambda x: x["count"], reverse=True)[:6]

    memeable = rng.choice(items) if items else {}
    meme = {
        "headline": str(memeable.get("title") or "No headline today"),
        "caption": "When the world insists on being a sketch show.",
        "rationale": "Picked for maximum absurdity potential (MVP heuristic).",
        "link": str(memeable.get("link") or ""),
    }

    if ai is None:
        brief = (
            "Today’s pulse: "
            + (", ".join([t["theme"] for t in top_themes[:3]]) or "misc")
            + ". We’re watching the headlines try to outdo themselves. Come for the facts, stay for the vibes."
        )
    else:
        prompt = (
            "Write a cheeky, sharp editor’s brief (2-3 sentences).\n"
            f"Voice: {voice}\n"
            f"Top themes: {[t['theme'] for t in top_themes]}\n"
        )
        brief = ai.generate(system="You are Pulseboard.", prompt=prompt, temperature=0.7).text

    return {
        "date": day,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "voice": voice,
        "editors_brief": brief,
        "top_themes": top_themes,
        "most_memeable": meme,
    }
