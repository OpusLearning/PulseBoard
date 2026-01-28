from pulsegen.ranking import pick_top3


def test_ranking_prefers_major_geopolitics_over_niche_hn():
    pulse = {
        "generated_utc": "2026-01-28T00:00:00Z",
        "items": [
            {"source": "HN", "title": "Native Linux VST plugin directory", "link": "l1", "published_utc": "2026-01-28T10:00:00Z"},
            {"source": "HN", "title": "Rust make TS faster", "link": "l2", "published_utc": "2026-01-28T09:00:00Z"},
            {"source": "BBC World", "title": "Trump warns Iran time is running out for nuclear deal", "link": "l3", "published_utc": "2026-01-28T08:00:00Z"},
            {"source": "Reuters", "title": "Markets fall as oil prices rise amid geopolitical tension", "link": "l4", "published_utc": "2026-01-28T08:30:00Z"},
            {"source": "AP", "title": "Election officials face scrutiny after recount", "link": "l5", "published_utc": "2026-01-28T07:00:00Z"}
        ]
    }
    top3 = pick_top3(pulse)
    titles = [t["title"] for t in top3]
    assert any("Iran" in t or "Trump" in t for t in titles)
    assert any("Markets" in t or "oil" in t.lower() for t in titles)
    assert not any("VST" in t for t in titles)
