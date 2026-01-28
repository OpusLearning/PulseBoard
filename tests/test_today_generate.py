from pulsegen.today import generate_today


def test_generate_today_heuristic_has_3_and_variants():
    pulse = {"generated_utc": "2026-01-28T00:00:00Z", "items": [
        {"source": "A", "title": "t1", "link": "l1", "published_utc": "2026-01-28T10:00:00Z"},
        {"source": "B", "title": "t2", "link": "l2", "published_utc": "2026-01-28T09:00:00Z"},
        {"source": "C", "title": "t3", "link": "l3", "published_utc": "2026-01-28T08:00:00Z"},
    ]}
    editor = {"editors_brief": "hi"}
    out = generate_today(pulse=pulse, editor=editor, audio=None, cards=None, day="2026-01-29", use_ai=False, ai=None)
    assert len(out["the3"]) == 3
    assert "variants" in out and all(k in out["variants"] for k in ["neutral","cheeky","contrarian","eli12"])
