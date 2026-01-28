from __future__ import annotations

from pathlib import Path
from typing import Any

from .io import read_json


def validate_jsonschema(*, schema_path: str | Path, data_path: str | Path) -> None:
    """Validate JSON against a JSON Schema.

    Uses `jsonschema` if available. This keeps runtime dependencies optional.
    """
    try:
        import jsonschema  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "jsonschema is not installed. Install it with: python -m pip install jsonschema"
        ) from e

    schema: Any = read_json(schema_path)
    data: Any = read_json(data_path)

    jsonschema.validate(instance=data, schema=schema)
