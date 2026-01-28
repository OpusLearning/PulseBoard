from pathlib import Path

from pulsegen.cards import render_cards


def test_render_cards_creates_pngs_and_cards_json(tmp_path: Path):
    editor = {
        "editors_brief": "Test brief.",
        "top_themes": [{"theme": "markets", "count": 2}],
        "most_memeable": {"headline": "Test headline", "caption": "Test cap"},
    }

    res = render_cards(editor=editor, out_dir=tmp_path, day="2026-01-29")
    assert res["ok"] is True

    p1 = tmp_path / "assets" / "cards" / "2026-01-29-01.png"
    p2 = tmp_path / "assets" / "cards" / "2026-01-29-02.png"
    p3 = tmp_path / "assets" / "cards" / "2026-01-29-03.png"
    assert p1.exists() and p2.exists() and p3.exists()

    cj = tmp_path / "data" / "cards.json"
    assert cj.exists()
