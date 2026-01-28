import zipfile
from pathlib import Path

from pulsegen.io import write_json_atomic
from pulsegen.exports import export_bundle


def test_export_bundle_creates_zip(tmp_path: Path):
    # Minimal editor
    write_json_atomic(tmp_path / 'data' / 'editor.json', {
        'date': '2026-01-29',
        'generated_utc': '2026-01-29T00:00:00Z',
        'voice': 'test',
        'editors_brief': 'Hello world',
        'top_themes': [],
        'most_memeable': {'headline': 'h', 'caption': 'c', 'rationale': 'r', 'link': 'https://x'},
    })

    zp = export_bundle(out_dir=tmp_path, day='2026-01-29')
    assert zp.exists()

    with zipfile.ZipFile(zp, 'r') as z:
        names = set(z.namelist())
        assert 'post.txt' in names
        assert 'meta.json' in names
        assert 'data/editor.json' in names
