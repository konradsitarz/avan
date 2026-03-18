"""ElevenLabs TTS client."""

import os
import logging

import httpx

logger = logging.getLogger(__name__)

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"


async def _get_first_voice(api_key: str) -> str | None:
    """Fetch the first available voice from the account."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{ELEVENLABS_BASE}/voices",
            headers={"xi-api-key": api_key},
        )
    logger.info(f"Voices lookup: status={resp.status_code}")
    if resp.status_code != 200:
        logger.error(f"Voices lookup failed: {resp.text[:300]}")
        return None
    voices = resp.json().get("voices", [])
    if voices:
        logger.info(f"Using voice: {voices[0]['name']} ({voices[0]['voice_id']})")
        return voices[0]["voice_id"]
    return None


async def synthesize(text: str, voice_id: str | None = None) -> bytes:
    """Generate speech audio from text. Returns raw MP3 bytes.

    Raises RuntimeError if API key is missing or generation fails.
    """
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        raise RuntimeError("ELEVENLABS_API_KEY not set")

    voice_id = voice_id or os.environ.get("ELEVENLABS_VOICE_ID") or None

    if not voice_id:
        voice_id = await _get_first_voice(api_key)
    if not voice_id:
        raise RuntimeError("No voices available on ElevenLabs account")

    url = f"{ELEVENLABS_BASE}/text-to-speech/{voice_id}"
    logger.info(f"TTS request: voice_id={voice_id}")

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
            },
            json={
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
        )

    if response.status_code != 200:
        logger.error(f"ElevenLabs API error: {response.status_code} {response.text[:300]}")
        raise RuntimeError("TTS generation failed")

    return response.content
