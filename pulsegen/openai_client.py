from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass

from .ai import AIClient, AIResult


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str
    model: str = "gpt-4.1-mini"


class OpenAIResponsesClient(AIClient):
    """Minimal OpenAI client using the Responses API.

    Keeps dependencies at zero. Good enough for server-side generation.
    """

    def __init__(self, cfg: OpenAIConfig):
        self.cfg = cfg

    def generate(self, *, system: str, prompt: str, temperature: float = 0.7) -> AIResult:
        url = "https://api.openai.com/v1/responses"

        payload = {
            "model": self.cfg.model,
            "input": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": float(temperature),
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.cfg.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # Extract text from the response output
        text_parts: list[str] = []
        for item in data.get("output", []) or []:
            for c in item.get("content", []) or []:
                if c.get("type") == "output_text" and c.get("text"):
                    text_parts.append(c["text"])

        text = "\n".join(text_parts).strip()
        return AIResult(text=text or "", data=data)


def client_from_env() -> OpenAIResponsesClient:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    model = os.environ.get("PULSEGEN_OPENAI_MODEL", "gpt-4.1-mini")
    return OpenAIResponsesClient(OpenAIConfig(api_key=key, model=model))
