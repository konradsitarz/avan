from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..core.tts import synthesize

router = APIRouter(prefix="/api/tts", tags=["tts"])


class TTSRequest(BaseModel):
    text: str
    voice_id: str | None = None


@router.post("")
async def text_to_speech(req: TTSRequest):
    try:
        audio = await synthesize(req.text, req.voice_id)
    except RuntimeError as e:
        status = 503 if "not set" in str(e) or "No voices" in str(e) else 502
        raise HTTPException(status_code=status, detail=str(e))

    return StreamingResponse(
        iter([audio]),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=briefing.mp3"},
    )
