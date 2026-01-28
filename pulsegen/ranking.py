from __future__ import annotations

import re
from datetime import datetime
from typing import Any

TOK_RE = re.compile(r"[A-Za-z][A-Za-z0-9']+")

MAJOR_SOURCES = {
    "BBC World",
    "BBC",
    "Reuters",
    "AP",
    "Associated Press",
    "Financial Times",
    "FT",
    "The Economist",
}

SOURCE_WEIGHT = {
    "BBC World": 4.5,
    "BBC": 4.0,
    "Reuters": 4.2,
    "AP": 3.8,
    "Associated Press": 3.8,
    "Financial Times": 4.2,
    "FT": 4.2,
    "The Economist": 4.0,
    "HN": 1.0,
    "Hacker News": 1.0,
}

NICHE_HINTS = {
    "linux", "vst", "plugin", "plugins", "rust", "typescript", "npm", "kubernetes", "devops",
    "audio", "synth", "vscode", "kernel", "postgres", "sqlite"
}

BROAD_HINTS = {
    "election", "war", "ukraine", "russia", "china", "iran", "israel", "gaza", "trump", "biden",
    "inflation", "rates", "market", "markets", "oil", "economy", "recession", "stocks", "ai",
    "tesla", "apple", "google", "amazon", "meta", "microsoft", "tiktok", "nato", "eu"
}


def _tokens(title: str) -> set[str]:
    return {t.lower() for t in TOK_RE.findall(title) if len(t) >= 3}


def _recency_bonus(published_utc: str | None) -> float:
    if not published_utc:
        return 0.0
    try:
        dt = datetime.fromisoformat(published_utc.replace('Z', '+00:00'))
        age_h = (datetime.utcnow().timestamp() - dt.timestamp()) / 3600.0
        if age_h < 6:
            return 0.6
        if age_h < 24:
            return 0.3
        return 0.0
    except Exception:
        return 0.0


def score_item(item: dict[str, Any], all_items: list[dict[str, Any]]) -> float:
    title = str(item.get('title') or '')
    source = str(item.get('source') or '')

    base = SOURCE_WEIGHT.get(source, 1.5)

    toks = _tokens(title)
    broad = len(toks & BROAD_HINTS)
    niche = len(toks & NICHE_HINTS)

    broad_bonus = min(2.0, broad * 0.45)
    niche_penalty = min(2.2, niche * 0.55)

    if source in MAJOR_SOURCES:
        niche_penalty *= 0.55

    cross = 0
    for other in all_items:
        if other is item:
            continue
        if str(other.get('source') or '') == source:
            continue
        otoks = _tokens(str(other.get('title') or ''))
        if not toks or not otoks:
            continue
        j = len(toks & otoks) / max(1, len(toks | otoks))
        if j >= 0.28:
            cross += 1
    cross_bonus = min(2.5, cross * 0.9)

    rec = _recency_bonus(str(item.get('published_utc') or ''))

    return base + broad_bonus + cross_bonus + rec - niche_penalty


def pick_top3(pulse: dict[str, Any]) -> list[dict[str, Any]]:
    items = list(pulse.get('items') or [])
    scored = [(score_item(it, items), it) for it in items]
    scored.sort(key=lambda x: x[0], reverse=True)

    out: list[dict[str, Any]] = []
    for _, it in scored:
        out.append({
            'title': str(it.get('title') or ''),
            'source': str(it.get('source') or ''),
            'link': str(it.get('link') or ''),
            'published_utc': str(it.get('published_utc') or ''),
        })
        if len(out) == 3:
            break

    while len(out) < 3:
        out.append({'title': '—', 'source': '', 'link': '', 'published_utc': ''})

    return out
