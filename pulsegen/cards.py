from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .io import write_json_atomic


@dataclass(frozen=True)
class CardSpec:
    w: int = 1080
    h: int = 1350  # 4:5


def _safe(s: Any) -> str:
    return str(s or "").strip()


def _wrap_words(text: str, max_chars: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    cur: list[str] = []
    for w in words:
        trial = (" ".join(cur + [w])).strip()
        if len(trial) <= max_chars:
            cur.append(w)
        else:
            if cur:
                lines.append(" ".join(cur))
            cur = [w]
    if cur:
        lines.append(" ".join(cur))
    return lines


def _load_today(data_dir: Path) -> dict[str, Any] | None:
    p = data_dir / "today.json"
    if not p.exists():
        return None
    import json
    try:
        return json.loads(p.read_text("utf-8"))
    except Exception:
        return None


def _font(size: int, bold: bool = False):
    from PIL import ImageFont

    p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    try:
        return ImageFont.truetype(p, size=size)
    except Exception:
        return ImageFont.load_default()


def _draw_poster(*, spec: CardSpec, kicker: str, headline: str, insight: str, footer: str, out_path: Path) -> None:
    """High-contrast, legible, poster-like card.

    Design constraints:
    - flat dark background
    - big headline
    - single insight line (short)
    - minimal metadata
    """
    from PIL import Image, ImageDraw

    bg = (9, 11, 16)  # near-black
    fg = (245, 245, 245)
    muted = (190, 190, 190)
    stroke = (255, 255, 255, 28)

    img = Image.new("RGBA", (spec.w, spec.h), bg + (255,))
    d = ImageDraw.Draw(img)

    # Subtle top accent bar (solid, not gradient)
    d.rounded_rectangle((60, 66, spec.w - 60, 78), radius=12, fill=(124, 58, 237, 255))

    # Outer frame (quiet)
    d.rounded_rectangle((44, 44, spec.w - 44, spec.h - 44), radius=28, outline=stroke, width=2)

    x = 84
    y = 120

    f_k = _font(30, True)
    f_h = _font(72, True)
    f_i = _font(40, False)
    f_f = _font(26, False)

    # Kicker
    d.text((x, y), kicker.upper(), font=f_k, fill=muted)
    y += 58

    # Headline (big)
    head_lines = _wrap_words(headline, 22)[:5]
    for ln in head_lines:
        d.text((x, y), ln, font=f_h, fill=fg)
        y += 84

    y += 10

    # Insight (one strong line, wrap lightly)
    ins_lines = _wrap_words(insight, 34)[:3]
    for ln in ins_lines:
        d.text((x, y), ln, font=f_i, fill=fg)
        y += 54

    # Footer
    d.text((x, spec.h - 110), footer, font=f_f, fill=muted)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.convert("RGB").save(out_path, format="PNG", optimize=True)


def render_cards(*, editor: dict[str, Any], out_dir: str | Path, day: str, spec: CardSpec = CardSpec()) -> dict[str, Any]:
    out_dir = Path(out_dir)
    cards_dir = out_dir / "assets" / "cards"
    data_dir = out_dir / "data"
    cards_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    today = _load_today(data_dir)

    lens = "neutral"
    angle = ""
    the3 = []
    if isinstance(today, dict):
        variants = today.get("variants") or {}
        v = variants.get(lens) or variants.get("neutral") or {}
        angle = _safe(v.get("angle"))
        the3 = list(today.get("the3") or [])

    brief = _safe(editor.get("editors_brief"))
    mm = editor.get("most_memeable") or {}
    mm_headline = _safe(getattr(mm, "get", lambda k, d=None: d)("headline", ""))

    footer = f"{day} · pulseboard.space"

    # Choose 3 posters that are glanceable
    # 01: Today angle (short)
    c1_head = "Today"
    c1_insight = angle or (brief[:140] if brief else "3 minutes to clarity.")

    # 02: Top story
    s0 = the3[0] if the3 and isinstance(the3[0], dict) else {}
    c2_head = _safe(s0.get("title")) or "The story"
    c2_insight = _safe(s0.get("what_to_say")) or _safe(s0.get("summary")) or "Here’s the line you can reuse."

    # 03: Memeable headline as a clean poster
    c3_head = "Most memeable"
    c3_insight = mm_headline or "—"

    paths = []
    p1 = cards_dir / f"{day}-01.png"
    _draw_poster(spec=spec, kicker="Pulseboard", headline=c1_head, insight=c1_insight, footer=footer, out_path=p1)
    paths.append({"id": f"{day}-01", "png": f"assets/cards/{p1.name}", "caption": "Today’s angle", "size": {"w": spec.w, "h": spec.h}})

    p2 = cards_dir / f"{day}-02.png"
    _draw_poster(spec=spec, kicker="The 3", headline=c2_head, insight=c2_insight, footer=footer, out_path=p2)
    paths.append({"id": f"{day}-02", "png": f"assets/cards/{p2.name}", "caption": "What to say", "size": {"w": spec.w, "h": spec.h}})

    p3 = cards_dir / f"{day}-03.png"
    _draw_poster(spec=spec, kicker="Shareable", headline=c3_head, insight=c3_insight, footer=footer, out_path=p3)
    paths.append({"id": f"{day}-03", "png": f"assets/cards/{p3.name}", "caption": "Most memeable", "size": {"w": spec.w, "h": spec.h}})

    cards_json = {
        "date": day,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cards": paths,
    }
    write_json_atomic(data_dir / "cards.json", cards_json)
    return {"ok": True, "cards": paths}
