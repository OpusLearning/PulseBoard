from __future__ import annotations

import io
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_json(p: Path) -> Any:
    return json.loads(p.read_text('utf-8'))


def build_post_copy(*, editor: dict[str, Any], audio: dict[str, Any] | None, cards: dict[str, Any] | None, base_url: str = 'https://pulseboard.space') -> str:
    date = editor.get('date') or ''
    brief = (editor.get('editors_brief') or '').strip()
    mm = editor.get('most_memeable') or {}
    mm_headline = (mm.get('headline') or '').strip()
    mm_link = (mm.get('link') or '').strip()

    lines = []
    lines.append(f"Pulseboard — {date}")
    if brief:
        lines.append(brief)
    lines.append("")
    if mm_headline:
        lines.append(f"Most memeable: {mm_headline}")
    if mm_link:
        lines.append(mm_link)
    lines.append("")

    if audio and audio.get('latest'):
        lines.append(f"Audio: {base_url}/" + str(audio['latest']).lstrip('/'))

    if cards and cards.get('cards'):
        lines.append("Cards:")
        for c in cards['cards'][:3]:
            png = (c.get('png') or '').lstrip('/')
            if png:
                lines.append(f"- {base_url}/{png}")

    lines.append("")
    lines.append("#Pulseboard")
    return "\n".join(lines).strip() + "\n"


def export_bundle(*, out_dir: str | Path, day: str, base_url: str = 'https://pulseboard.space') -> Path:
    out_dir = Path(out_dir)
    data_dir = out_dir / 'data'
    assets_dir = out_dir / 'assets'

    editor_path = data_dir / 'editor.json'
    if not editor_path.exists():
        raise FileNotFoundError(f"missing {editor_path}")

    editor = _read_json(editor_path)

    audio = None
    ap = data_dir / 'audio.json'
    if ap.exists():
        audio = _read_json(ap)

    cards = None
    cp = data_dir / 'cards.json'
    if cp.exists():
        cards = _read_json(cp)

    export_dir = out_dir / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)
    zip_path = export_dir / f"{day}.zip"

    post_copy = build_post_copy(editor=editor, audio=audio, cards=cards, base_url=base_url)

    with zipfile.ZipFile(zip_path, 'w', compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr('post.txt', post_copy)
        z.writestr('meta.json', json.dumps({
            'date': day,
            'generated_utc': datetime.now(timezone.utc).isoformat(),
            'includes': {
                'editor': True,
                'audio': bool(audio and audio.get('latest')),
                'cards': bool(cards and cards.get('cards')),
            }
        }, indent=2) + "\n")

        # Include artefacts if present
        z.write(editor_path, arcname='data/editor.json')
        if audio:
            z.write(ap, arcname='data/audio.json')
            latest = (audio.get('latest') or '')
            if latest:
                mp3 = out_dir / latest
                if mp3.exists():
                    z.write(mp3, arcname=latest)
                txt = mp3.with_suffix('.txt')
                if txt.exists():
                    z.write(txt, arcname=str(txt.relative_to(out_dir)))

        if cards and cards.get('cards'):
            z.write(cp, arcname='data/cards.json')
            for c in cards['cards'][:3]:
                png = (c.get('png') or '')
                if not png:
                    continue
                p = out_dir / png
                if p.exists():
                    z.write(p, arcname=png)

    return zip_path
