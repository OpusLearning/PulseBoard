from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Any


@dataclass(frozen=True)
class AIResult:
    """Structured result from an AI call."""

    text: str
    data: dict[str, Any] | None = None


class AIClient(Protocol):
    def generate(self, *, system: str, prompt: str, temperature: float = 0.7) -> AIResult:
        ...


class FakeAIClient:
    """Deterministic fake for unit tests."""

    def __init__(self, rules: list[tuple[str, AIResult]] | None = None):
        self.rules = rules or []
        self.calls: list[dict[str, object]] = []

    def generate(self, *, system: str, prompt: str, temperature: float = 0.7) -> AIResult:
        self.calls.append({"system": system, "prompt": prompt, "temperature": temperature})
        for needle, result in self.rules:
            if needle in prompt:
                return result
        return AIResult(text="(fake) no rule matched", data=None)
