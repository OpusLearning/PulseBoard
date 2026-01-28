from pulsegen.audio import render_script


def test_render_script_short_and_mentions_memeable():
    editor = {
        "editors_brief": "Today is chaotic but funny.",
        "most_memeable": {"headline": "A cat runs for mayor"},
    }
    s = render_script(editor, max_words=40)
    assert "Most memeable" in s
    assert len(s.split()) <= 40
