import subprocess
import sys


def test_today_schema_validates_example():
    subprocess.check_call([sys.executable, '-m', 'pulsegen', 'validate-schema', '--schema', 'schemas/today.schema.json', '--file', 'examples/today.example.json'])
