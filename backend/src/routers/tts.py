import os
import logging

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tts", tags=["tts"])

ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"


class TTSRequest(BaseModel):
    text: str
    voice_id: str | None = None


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


@router.post("")
async def text_to_speech(req: TTSRequest):
    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        logger.error("ELEVENLABS_API_KEY not set")
        raise HTTPException(status_code=503, detail="ElevenLabs API key not configured")

    voice_id = req.voice_id or os.environ.get("ELEVENLABS_VOICE_ID") or None

    # If no voice configured, fetch the first one from the account
    if not voice_id:
        voice_id = await _get_first_voice(api_key)
    if not voice_id:
        raise HTTPException(status_code=503, detail="No voices available on ElevenLabs account")

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
                "text": req.text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
        )

    if response.status_code != 200:
        logger.error(f"ElevenLabs API error: {response.status_code} {response.text[:300]}")
        raise HTTPException(status_code=502, detail="TTS generation failed")

    return StreamingResponse(
        iter([response.content]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=briefing.mp3"},
    )
