import json
import subprocess
import sys
from pathlib import Path


def test_cli_run_creates_editor_json(tmp_path: Path):
    out = tmp_path / "out"
    out.mkdir()

    cmd = [sys.executable, "-m", "pulsegen", "run", "--date", "2026-01-29", "--in", "examples/pulse.sample.json", "--out", str(out), "--seed", "123"]
    subprocess.check_call(cmd)

    p = out / "data" / "editor.json"
    assert p.exists()
    data = json.loads(p.read_text("utf-8"))
    assert data["date"] == "2026-01-29"
