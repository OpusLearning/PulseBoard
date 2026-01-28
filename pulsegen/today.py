from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .ai import AIClient


LENSES = ["neutral", "cheeky", "contrarian", "eli12"]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _top3_from_pulse(pulse: dict[str, Any]) -> list[dict[str, Any]]:
    items = list(pulse.get("items") or [])

    def key(it: dict[str, Any]) -> float:
        ts = it.get("published_utc") or ""
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except Exception:
            return 0.0

    items = sorted(items, key=key, reverse=True)
    out = []
    for it in items[:3]:
        out.append({
            "title": str(it.get("title") or ""),
            "source": str(it.get("source") or ""),
            "link": str(it.get("link") or ""),
        })
    # pad if needed
    while len(out) < 3:
        out.append({"title": "—", "source": "", "link": ""})
    return out


def _heuristic_story_fields(st: dict[str, Any]) -> dict[str, Any]:
    title = st.get("title") or "—"
    return {
        **st,
        "summary": f"{title[:90]}" if title else "—",
        "why_it_matters": "Because it changes incentives people actually feel.",
        "watch_for": "A follow-up announcement or reversal within 48 hours.",
        "what_to_say": "The interesting part is the second-order impact, not the headline.",
        "confidence": 0.62,
        "confidence_reason": "Heuristic (no multi-source verification step yet).",
    }


def _ai_generate_today(*, pulse: dict[str, Any], editor: dict[str, Any], day: str, ai: AIClient) -> dict[str, Any]:
    top3 = _top3_from_pulse(pulse)
    prompt = {
        "day": day,
        "north_star": "3 minutes: informed, amused, ahead",
        "instructions": [
            "Return ONLY valid JSON matching this shape.",
            "Write short, rhythmic lines. No cringe.",
            "Make it socially usable: include what_to_say lines.",
            "Be truthful: do not invent facts beyond titles/links given.",
        ],
        "inputs": {
            "editors_brief": editor.get("editors_brief", ""),
            "top3": top3,
        },
        "required": {
            "variants": {
                "neutral": {"angle": "string", "what_to_say": ["string"], "signal": 0.0, "time_s": 180},
                "cheeky": {"angle": "string", "what_to_say": ["string"], "signal": 0.0, "time_s": 180},
                "contrarian": {"angle": "string", "what_to_say": ["string"], "signal": 0.0, "time_s": 180},
                "eli12": {"angle": "string", "what_to_say": ["string"], "signal": 0.0, "time_s": 180}
            },
            "the3": [
                {
                    "title": "string",
                    "source": "string",
                    "link": "string",
                    "summary": "string",
                    "why_it_matters": "string",
                    "watch_for": "string",
                    "what_to_say": "string",
                    "confidence": 0.0,
                    "confidence_reason": "string"
                }
            ]
        }
    }

    raw = ai.generate(system="You are Pulseboard. Be precise. Output JSON only.", prompt=json.dumps(prompt), temperature=0.5).text
    data = json.loads(raw)
    return data


def generate_today(*, pulse: dict[str, Any], editor: dict[str, Any], audio: dict[str, Any] | None, cards: dict[str, Any] | None,
                   day: str, use_ai: bool, ai: AIClient | None) -> dict[str, Any]:
    if use_ai and ai is None:
        raise RuntimeError("AI requested but no client provided")

    if use_ai:
        core = _ai_generate_today(pulse=pulse, editor=editor, day=day, ai=ai)  # may raise
        the3 = core.get("the3") or []
        variants = core.get("variants") or {}
    else:
        the3 = [_heuristic_story_fields(s) for s in _top3_from_pulse(pulse)]
        variants = {
            "neutral": {"angle": "Your Pulse is ready. High signal, low noise.", "what_to_say": ["Here’s the key point and why it matters."], "signal": 0.75, "time_s": 180},
            "cheeky": {"angle": "Your Pulse is ready. The plot thickens." , "what_to_say": ["Here’s the line you can reuse: this matters because…"], "signal": 0.70, "time_s": 180},
            "contrarian": {"angle": "Your Pulse is ready. Everyone’s staring at the wrong lever.", "what_to_say": ["Hot take: watch the incentives, not the quotes."], "signal": 0.82, "time_s": 180},
            "eli12": {"angle": "Your Pulse is ready. The simple version:", "what_to_say": ["In one sentence: here’s what happened and why."], "signal": 0.72, "time_s": 180}
        }

    # audio pointers
    audio_latest = (audio or {}).get("latest") if isinstance(audio, dict) else ""
    transcript = ""
    if audio_latest:
        transcript = str(audio_latest).replace('.mp3', '.txt')

    # cards pointers
    cards_list: list[str] = []
    if isinstance(cards, dict):
        for c in (cards.get("cards") or [])[:3]:
            if isinstance(c, dict) and c.get("png"):
                cards_list.append(str(c["png"]))

    now = _iso_now()
    out = {
        "date": day,
        "generated_utc": now,
        "updated_utc": (pulse.get("generated_utc") or now),
        "variants": variants,
        "the3": the3[:3],
        "audio": {"latest": str(audio_latest or ""), "transcript": str(transcript or "")},
        "cards": cards_list,
    }
    return out
