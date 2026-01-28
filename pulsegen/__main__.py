from __future__ import annotations

import argparse

from .pipeline import run
from .io import read_json
from .validate import validate_editor
from .schema_validate import validate_jsonschema


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="pulsegen")
    sub = p.add_subparsers(dest="cmd", required=True)

    prun = sub.add_parser("run", help="Run daily generation pipeline")
    prun.add_argument("--date", required=True, help="YYYY-MM-DD")
    prun.add_argument("--in", dest="infile", required=True, help="Input pulse.json")
    prun.add_argument("--out", dest="outdir", required=True, help="Output directory")
    prun.add_argument("--voice", default="witty-cheeky-sharp")
    prun.add_argument("--seed", type=int, default=0)
    prun.add_argument("--ai", action="store_true", help="Use OpenAI (requires OPENAI_API_KEY)")
    prun.add_argument("--tts", action="store_true", help="Generate MP3 via ElevenLabs (requires ELEVENLABS_API_KEY + ELEVENLABS_VOICE_ID)")
    prun.add_argument("--cards", action="store_true", help="Generate quote cards PNGs (requires Pillow)")
    prun.add_argument("--export", action="store_true", help="Create a daily export ZIP bundle")

    pval = sub.add_parser("validate-editor", help="Validate an editor.json file")
    pval.add_argument("--file", required=True)

    pschema = sub.add_parser("validate-schema", help="Validate JSON file with JSON Schema")
    pschema.add_argument("--schema", required=True)
    pschema.add_argument("--file", required=True)

    args = p.parse_args(argv)

    if args.cmd == "run":
        res = run(day=args.date, pulse_in=args.infile, out_dir=args.outdir, voice=args.voice, seed=args.seed, use_ai=args.ai, use_tts=args.tts, use_cards=args.cards, use_export=args.export)
        print(res)
        return 0

    if args.cmd == "validate-editor":
        data = read_json(args.file)
        validate_editor(data)
        print({"ok": True})
        return 0

    if args.cmd == "validate-schema":
        validate_jsonschema(schema_path=args.schema, data_path=args.file)
        print({"ok": True})
        return 0

    raise SystemExit(2)


if __name__ == "__main__":
    raise SystemExit(main())
