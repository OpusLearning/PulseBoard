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


def _pick_palette(i: int) -> tuple[tuple[int,int,int], tuple[int,int,int]]:
    # Deliberate, high-contrast gradients (dark + neon)
    palettes = [
        ((124, 58, 237), (6, 182, 212)),   # violet -> cyan
        ((249, 115, 22), (124, 58, 237)),  # orange -> violet
        ((34, 197, 94), (6, 182, 212)),    # green -> cyan
    ]
    return palettes[i % len(palettes)]


def _linear_gradient(img, c0, c1) -> None:
    # Simple vertical gradient
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(c0[0] * (1 - t) + c1[0] * t)
        g = int(c0[1] * (1 - t) + c1[1] * t)
        b = int(c0[2] * (1 - t) + c1[2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def _noise_overlay(img, alpha: int = 22) -> None:
    # Subtle grain for “premium” feel
    from PIL import Image, ImageChops
    import os

    w, h = img.size
    noise = Image.effect_noise((w, h), 20)
    noise = noise.convert("L")
    noise = ImageChops.add(noise, Image.new("L", (w, h), 128), scale=2.0)
    overlay = Image.merge("RGBA", (noise, noise, noise, Image.new("L", (w, h), alpha)))
    img.alpha_composite(overlay)


def _wrap_text(text: str, max_chars: int) -> list[str]:
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
    return lines[:8]


def _draw_card(*, spec: CardSpec, title: str, subtitle: str, footer: str, variant: int) -> "bytes":
    from PIL import Image, ImageDraw, ImageFont

    base = Image.new("RGBA", (spec.w, spec.h), (0, 0, 0, 255))
    c0, c1 = _pick_palette(variant)
    _linear_gradient(base, c0, c1)

    # Dark glass panel
    panel = Image.new("RGBA", (spec.w, spec.h), (0, 0, 0, 0))
    d = ImageDraw.Draw(panel)
    pad = 60
    d.rounded_rectangle(
        (pad, pad, spec.w - pad, spec.h - pad),
        radius=36,
        fill=(10, 12, 18, 200),
        outline=(255, 255, 255, 26),
        width=2,
    )
    base.alpha_composite(panel)

    _noise_overlay(base)

    draw = ImageDraw.Draw(base)

    # Font: try DejaVu (installed on Ubuntu) as deliberate “editorial” default
    def font(size: int, bold: bool = False):
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        p = paths[1] if bold else paths[0]
        try:
            return ImageFont.truetype(p, size=size)
        except Exception:
            return ImageFont.load_default()

    f_kicker = font(36, bold=True)
    f_title = font(64, bold=True)
    f_sub = font(40, bold=False)
    f_footer = font(30, bold=False)

    x0 = 100
    y = 120

    # Kicker (small caps vibe)
    kicker = "PULSEBOARD"
    draw.text((x0, y), kicker, fill=(255, 255, 255, 220), font=f_kicker)
    y += 70

    # Title
    t_lines = _wrap_text(title, 26)
    for ln in t_lines:
        draw.text((x0, y), ln, fill=(255, 255, 255, 240), font=f_title)
        y += 78

    y += 10

    # Subtitle
    s_lines = _wrap_text(subtitle, 34)
    for ln in s_lines:
        draw.text((x0, y), ln, fill=(255, 255, 255, 200), font=f_sub)
        y += 52

    # Footer
    draw.text((x0, spec.h - 120), footer, fill=(255, 255, 255, 170), font=f_footer)

    return base.convert("RGB").tobytes()  # placeholder


def render_cards(*, editor: dict[str, Any], out_dir: str | Path, day: str, spec: CardSpec = CardSpec()) -> dict[str, Any]:
    """Generate 3 quote cards + cards.json.

    No external APIs. Designed visuals (dark + neon gradients + grain).
    """
    from PIL import Image

    out_dir = Path(out_dir)
    cards_dir = out_dir / "assets" / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    data_dir = out_dir / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    brief = _safe(editor.get("editors_brief"))
    mm = editor.get("most_memeable") or {}
    mm_headline = _safe(getattr(mm, "get", lambda k, d=None: d)("headline", ""))
    mm_caption = _safe(getattr(mm, "get", lambda k, d=None: d)("caption", ""))
    themes = [(_safe(t.get("theme")), int(t.get("count", 0))) for t in (editor.get("top_themes") or []) if isinstance(t, dict)]
    themes = [t for t in themes if t[0]]

    cards_meta: list[dict[str, Any]] = []

    def save_card(idx: int, title: str, subtitle: str, footer: str) -> str:
        from PIL import Image, ImageDraw

        # Recreate image using helper that returns an RGB bytes buffer; easier is to draw directly here.
        # We'll build a full image and save.
        img = Image.new("RGBA", (spec.w, spec.h), (0, 0, 0, 255))
        c0, c1 = _pick_palette(idx - 1)
        _linear_gradient(img, c0, c1)
        # dark panel
        panel = Image.new("RGBA", (spec.w, spec.h), (0, 0, 0, 0))
        d = ImageDraw.Draw(panel)
        pad = 60
        d.rounded_rectangle((pad, pad, spec.w - pad, spec.h - pad), radius=36, fill=(10,12,18,200), outline=(255,255,255,26), width=2)
        img.alpha_composite(panel)
        _noise_overlay(img)

        from PIL import ImageFont
        draw = ImageDraw.Draw(img)
        def font(size: int, bold: bool = False):
            p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            try:
                return ImageFont.truetype(p, size=size)
            except Exception:
                return ImageFont.load_default()
        f_kicker = font(36, True)
        f_title = font(64, True)
        f_sub = font(40, False)
        f_footer = font(30, False)

        x0 = 100
        y = 120
        draw.text((x0, y), "PULSEBOARD", fill=(255,255,255,220), font=f_kicker)
        y += 70
        for ln in _wrap_text(title, 26):
            draw.text((x0, y), ln, fill=(255,255,255,240), font=f_title)
            y += 78
        y += 10
        for ln in _wrap_text(subtitle, 34):
            draw.text((x0, y), ln, fill=(255,255,255,200), font=f_sub)
            y += 52
        draw.text((x0, spec.h - 120), footer, fill=(255,255,255,170), font=f_footer)

        out_path = cards_dir / f"{day}-{idx:02d}.png"
        img.convert("RGB").save(out_path, format="PNG", optimize=True)
        return f"assets/cards/{out_path.name}"

    footer = f"{day} · pulseboard.space"

    # Card 1: brief
    rel = save_card(1, "Today’s take", brief or "No brief yet.", footer)
    cards_meta.append({"id": f"{day}-01", "png": rel, "caption": "Today’s AI take", "size": {"w": spec.w, "h": spec.h}})

    # Card 2: memeable
    rel = save_card(2, "Most memeable", mm_headline or "—", footer)
    cards_meta.append({"id": f"{day}-02", "png": rel, "caption": mm_caption or "Most memeable", "size": {"w": spec.w, "h": spec.h}})

    # Card 3: themes
    theme_line = " · ".join([f"{t}({c})" for t, c in themes[:4]]) or "—"
    rel = save_card(3, "Top themes", theme_line, footer)
    cards_meta.append({"id": f"{day}-03", "png": rel, "caption": "Top themes", "size": {"w": spec.w, "h": spec.h}})

    cards_json = {
        "date": day,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "cards": cards_meta,
    }
    write_json_atomic(data_dir / "cards.json", cards_json)
    return {"ok": True, "cards": cards_meta}
