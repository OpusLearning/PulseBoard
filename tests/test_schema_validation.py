import subprocess
import sys


def test_validate_schema_command():
    # Ensure jsonschema is available for this test
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "jsonschema"])

    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "pulsegen",
            "validate-schema",
            "--schema",
            "schemas/editor.schema.json",
            "--file",
            "examples/editor.example.json",
        ]
    )
