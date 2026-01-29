from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .openai_images import images_from_env
from .io import write_json_atomic


HOUSE_STYLE = {
    "style": "UI-native symbolic visual (thin-line vector / monoline)",
    "background": "charcoal/near-black to blend with Pulseboard UI",
    "palette": "monochrome + ONE accent glow (violet/blue/amber)",
    "composition": "one metaphor, one focal idea, lots of negative space, crop-safe margins",
    "typography": "do NOT bake headlines into the image; keep images text-free",
    "avoid": "no retro posters, no beige/paper texture, no collage, no photorealism, no painterly Midjourney look",
    "tone": "dry, observational, wry (never goofy)",
}


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_visual_briefs(today: dict[str, Any], *, ai_text) -> dict[str, Any]:
    """Mutates/returns today with visual_brief per story + composite_brief."""
    the3 = today.get("the3") or []
    if not isinstance(the3, list):
        return today

    # Build prompt
    stories = []
    for s in the3[:3]:
        if not isinstance(s, dict):
            continue
        stories.append({
            "title": s.get("title", ""),
            "source": s.get("source", ""),
            "link": s.get("link", ""),
            "summary": s.get("summary", ""),
            "what_to_say": s.get("what_to_say", ""),
        })

    contract = {
        "stories": [
            {
                "visual_brief": {
                    "core_idea": "...",
                    "visual_metaphor": "...",
                    "scene_description": "...",
                    "tone": "tense|ironic|calm|unsettling|...",
                    "overlay_text": "empty string (typography stays in UI)"
                }
            }
        ],
        "composite": {
            "core_idea": "...",
            "visual_metaphor": "...",
            "scene_description": "...",
            "tone": "...",
            "overlay_text": "empty string (typography stays in UI)"
        }
    }

    prompt = {
        "positioning": "High-signal intelligence, presented with taste and subtle wit.",
        "house_style": HOUSE_STYLE,
        "rules": [
            "Return ONLY valid JSON.",
            "Symbolic metaphor. One focal idea per image.",
            "No photorealism. No collage.",
            "Do NOT include embedded text in the image. Typography stays in the UI.",
            "No slang. No emojis.",
        ],
        "stories": stories,
        "output_contract": contract,
    }

    raw = ai_text.generate(
        system="You are an editorial art director. Output JSON only.",
        prompt=json.dumps(prompt),
        temperature=0.3,
    ).text.strip()

    data = json.loads(raw)

    # apply briefs back
    out3 = []
    for i, s in enumerate(the3[:3]):
        s2 = dict(s)
        try:
            vb = data.get("stories", [])[i].get("visual_brief")
        except Exception:
            vb = None
        if isinstance(vb, dict):
            s2["visual_brief"] = vb
        out3.append(s2)

    today["the3"] = out3
    if isinstance(data.get("composite"), dict):
        today["composite_brief"] = data["composite"]

    return today


def _image_prompt_for_brief(title: str, brief: dict[str, Any]) -> str:
    overlay = (brief.get("overlay_text") or "").strip()
    overlay_rule = "Include overlay text: '" + overlay + "'." if overlay else "No overlay text."

    return "\n".join([
        "Editorial illustration for Pulseboard.",
        f"Topic/title: {title}",
        f"Core idea: {brief.get('core_idea','')}",
        f"Metaphor: {brief.get('visual_metaphor','')}",
        f"Scene: {brief.get('scene_description','')}",
        f"Tone: {brief.get('tone','')}",
        overlay_rule,
        "Style: thin-line vector / monoline illustration, minimalist, not photorealistic.",
        "Composition: clean, one focal idea, negative space.",
        "Palette: charcoal/near-black background, off-white linework, ONE subtle accent glow (violet/blue/amber).",
        "No gradients that band. No collage. No stock-photo aesthetic.",
        "High contrast, mobile-legible.",
        "Safe area: keep all important content at least 12% away from edges.",
        "No text baked into image.",
    ])


def generate_story_images(today: dict[str, Any], *, out_dir: Path, day: str) -> dict[str, Any]:
    assets_story = out_dir / "assets" / "story"
    assets_story.mkdir(parents=True, exist_ok=True)

    img = images_from_env()

    out_paths: list[str] = []
    for idx, s in enumerate((today.get("the3") or [])[:3], start=1):
        if not isinstance(s, dict):
            continue
        vb = s.get("visual_brief")
        if not isinstance(vb, dict):
            continue

        out_path = assets_story / f"{day}-{idx:02d}.png"
        rel = f"assets/story/{out_path.name}"        force = os.environ.get("PULSEGEN_FORCE_IMAGES", "0") == "1"
        if (not force) and out_path.exists() and out_path.stat().st_size > 0:
            out_paths.append(rel)
            continue

        prompt = _image_prompt_for_brief(str(s.get("title") or ""), vb)
        png = img.generate_png(prompt=prompt, size="1024x1024")
        out_path.write_bytes(png)
        out_paths.append(rel)

    today["story_images"] = out_paths
    return today


def generate_composite_image(today: dict[str, Any], *, out_dir: Path, day: str) -> dict[str, Any]:
    assets_comp = out_dir / "assets" / "composite"
    assets_comp.mkdir(parents=True, exist_ok=True)

    brief = today.get("composite_brief")
    if not isinstance(brief, dict):
        return today

    out_path = assets_comp / f"{day}.png"
    rel = f"assets/composite/{out_path.name}"    force = os.environ.get("PULSEGEN_FORCE_IMAGES", "0") == "1"

    if force or (not out_path.exists()) or out_path.stat().st_size == 0:
        img = images_from_env()
        prompt = _image_prompt_for_brief("Daily composite", brief)
        png = img.generate_png(prompt=prompt, size="1024x1024")
        out_path.write_bytes(png)

    today["composite_image"] = rel
    return today
