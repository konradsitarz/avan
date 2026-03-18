import logging

from fastapi import APIRouter, HTTPException

from ..services import BriefingService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("")
async def get_briefing():
    try:
        return await BriefingService.get_briefing()
    except Exception as e:
        logger.exception("Briefing generation failed")
        raise HTTPException(status_code=500, detail=str(e))
