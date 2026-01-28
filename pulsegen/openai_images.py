from __future__ import annotations

import base64
import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class OpenAIImageConfig:
    api_key: str
    model: str = "gpt-image-1"


class OpenAIImages:
    def __init__(self, cfg: OpenAIImageConfig):
        self.cfg = cfg

    def generate_png(self, *, prompt: str, size: str = "1024x1024") -> bytes:
        """Returns PNG bytes."""
        url = "https://api.openai.com/v1/images/generations"
        payload = {
            "model": self.cfg.model,
            "prompt": prompt,
            "size": size,
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        # images API returns base64 in data[0].b64_json
        b64 = (data.get("data") or [{}])[0].get("b64_json")
        if not b64:
            raise RuntimeError("No image returned")
        return base64.b64decode(b64)


def images_from_env() -> OpenAIImages:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY is not set")
    model = os.environ.get("PULSEGEN_OPENAI_IMAGE_MODEL", "gpt-image-1")
    return OpenAIImages(OpenAIImageConfig(api_key=key, model=model))
