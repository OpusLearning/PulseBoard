from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ValidationError(Exception):
    message: str


def require(obj: dict[str, Any], key: str, types: tuple[type, ...]) -> None:
    if key not in obj:
        raise ValidationError(f"missing required key: {key}")
    if not isinstance(obj[key], types):
        raise ValidationError(f"key {key} expected {types}, got {type(obj[key]).__name__}")


def validate_editor(data: dict[str, Any]) -> None:
    require(data, "date", (str,))
    require(data, "generated_utc", (str,))
    require(data, "voice", (str,))
    require(data, "editors_brief", (str,))
    require(data, "top_themes", (list,))
    require(data, "most_memeable", (dict,))
    mm = data["most_memeable"]
    require(mm, "headline", (str,))
    require(mm, "caption", (str,))
    require(mm, "rationale", (str,))
    require(mm, "link", (str,))
