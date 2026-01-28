from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass


@dataclass(frozen=True)
class ElevenLabsConfig:
    api_key: str
    voice_id: str
    model_id: str = "eleven_multilingual_v2"


class ElevenLabsTTS:
    """Minimal ElevenLabs TTS client (no external deps)."""

    def __init__(self, cfg: ElevenLabsConfig):
        self.cfg = cfg

    def synth_mp3(self, *, text: str) -> bytes:
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.cfg.voice_id}"
        payload = {
            "text": text,
            "model_id": self.cfg.model_id,
            "voice_settings": {"stability": 0.4, "similarity_boost": 0.75},
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "xi-api-key": self.cfg.api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=90) as resp:
            return resp.read()


def tts_from_env() -> ElevenLabsTTS:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if not key:
        raise RuntimeError("ELEVENLABS_API_KEY is not set")
    voice_id = os.environ.get("ELEVENLABS_VOICE_ID")
    if not voice_id:
        raise RuntimeError("ELEVENLABS_VOICE_ID is not set")
    model = os.environ.get("PULSEGEN_ELEVEN_MODEL", "eleven_multilingual_v2")
    return ElevenLabsTTS(ElevenLabsConfig(api_key=key, voice_id=voice_id, model_id=model))
