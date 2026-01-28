from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from .ai import AIClient
from .ranking import pick_top3


LENSES = ["neutral", "cheeky", "contrarian", "eli12"]


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    """Ask the model to write *framing*, not new facts.

    Rules:
    - You MAY only use facts present in the given headlines/sources/links.
    - You MAY add interpretation, stakes, incentives, and socially-usable phrasing.
    - Keep each field short, rhythmic, and non-cringe.
    - Output JSON only.
    """

    top3 = pick_top3(pulse)

    contract = {
        "variants": {
            "neutral": {"angle": "string (1 sentence)", "what_to_say": ["string"], "signal": 0.0, "time_s": 180},
            "cheeky": {"angle": "string (1 sentence)", "what_to_say": ["string"], "signal": 0.0, "time_s": 180},
            "contrarian": {"angle": "string (1 sentence)", "what_to_say": ["string"], "signal": 0.0, "time_s": 180},
            "eli12": {"angle": "string (1 sentence)", "what_to_say": ["string"], "signal": 0.0, "time_s": 180}
        },
        "the3": [
            {
                "title": "string (copied from input)",
                "source": "string (copied from input)",
                "link": "string (copied from input)",
                "summary": "string (INSIGHT sentence, not a description)",
                "why_it_matters": "string (1 line, stakes)",
                "watch_for": "string (1 line, what changes next)",
                "what_to_say": "string (1 line you can repeat)",
                "confidence": 0.0,
                "confidence_reason": "string (1 line, why this confidence)"
            }
        ]
    }

    prompt = {
        "day": day,
        "north_star": "3 minutes to clarity; help user sound smart in conversation",
        "tone_rules": [
            "UI is calm premium. Copy can be punchy but never cringe.",
            "No filler like 'in today's world'.",
            "Short sentences. Strong verbs."
        ],
        "truth_rules": [
            "Do not invent facts beyond the provided headlines/sources/links.",
            "Do not claim numbers, quotes, or outcomes not present.",
            "If uncertain, phrase as implications/stakes (not assertions)."
        ],
        "input": {
            "editors_brief": editor.get("editors_brief", ""),
            "top3": top3
        },
        "output_contract": contract
    }

    raw = ai.generate(
        system="You are an editorial briefing engine. Output JSON only. No markdown.",
        prompt=json.dumps(prompt),
        temperature=0.4,
    ).text.strip()

    return json.loads(raw)


def _postprocess_ai(core: dict[str, Any], top3: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    # Variants: ensure required keys and non-zero-ish signal/time
    variants = core.get("variants") if isinstance(core, dict) else None
    if not isinstance(variants, dict):
        variants = {}
    for k in LENSES:
        v = variants.get(k)
        if not isinstance(v, dict):
            v = {}
        if not isinstance(v.get("angle"), str):
            v["angle"] = "You’re up to speed. Here’s what matters." if k == "neutral" else "You’re up to speed."
        wts = v.get("what_to_say")
        if not isinstance(wts, list) or not wts:
            v["what_to_say"] = ["Here’s the key point, and why it matters."]
        # normalize
        try:
            sig = float(v.get("signal", 0.0))
        except Exception:
            sig = 0.0
        if sig <= 0.0:
            v["signal"] = 0.75
        try:
            ts = int(v.get("time_s", 0))
        except Exception:
            ts = 0
        if ts <= 0:
            v["time_s"] = 180
        variants[k] = v

    # The 3: ensure 3 items and force-copy title/source/link from input
    the3 = core.get("the3") if isinstance(core, dict) else None
    if not isinstance(the3, list):
        the3 = []

    out3: list[dict[str, Any]] = []
    for i in range(3):
        base = top3[i] if i < len(top3) else {"title": "—", "source": "", "link": ""}
        row = the3[i] if i < len(the3) and isinstance(the3[i], dict) else {}
        row = dict(row)
        row["title"] = base.get("title", "")
        row["source"] = base.get("source", "")
        row["link"] = base.get("link", "")

        # clamp confidence
        try:
            c = float(row.get("confidence", 0.62))
        except Exception:
            c = 0.62
        c = max(0.0, min(1.0, c))
        if c == 0.0:
            c = 0.62
        row["confidence"] = c

        # required strings
        for k in ["summary", "why_it_matters", "watch_for", "what_to_say", "confidence_reason"]:
            if not isinstance(row.get(k), str) or not str(row.get(k)).strip():
                row[k] = _heuristic_story_fields(base)[k]
        out3.append(row)

    return variants, out3


def generate_today(*, pulse: dict[str, Any], editor: dict[str, Any], audio: dict[str, Any] | None, cards: dict[str, Any] | None,
                   day: str, use_ai: bool, ai: AIClient | None) -> dict[str, Any]:
    if use_ai and ai is None:
        raise RuntimeError("AI requested but no client provided")

    if use_ai:
        core = _ai_generate_today(pulse=pulse, editor=editor, day=day, ai=ai)  # may raise
        variants, the3 = _postprocess_ai(core, pick_top3(pulse))
    else:
        the3 = [_heuristic_story_fields(s) for s in pick_top3(pulse)]
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
        # include all generated cards (UI may choose how many to display)
        for c in (cards.get("cards") or []):
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
