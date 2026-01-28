from pathlib import Path

from pulsegen.io import write_json_atomic, read_json


def test_write_json_atomic_roundtrip(tmp_path: Path):
    p = tmp_path / "out.json"
    write_json_atomic(p, {"a": 1})
    assert read_json(p) == {"a": 1}
    assert p.exists()
    assert p.stat().st_size > 0
