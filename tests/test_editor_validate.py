from pulsegen.io import read_json
from pulsegen.editor import generate_editor
from pulsegen.validate import validate_editor


def test_generate_editor_is_valid_and_deterministic():
    pulse = read_json("examples/pulse.sample.json")

    a = generate_editor(pulse=pulse, day="2026-01-29", voice="witty-cheeky-sharp", seed=123, ai=None)
    b = generate_editor(pulse=pulse, day="2026-01-29", voice="witty-cheeky-sharp", seed=123, ai=None)

    validate_editor(a)
    validate_editor(b)

    a2 = dict(a)
    b2 = dict(b)
    a2.pop("generated_utc", None)
    b2.pop("generated_utc", None)
    assert a2 == b2
