from fastapi import APIRouter

from ..services import BriefingService

router = APIRouter(prefix="/api/briefing", tags=["briefing"])


@router.get("")
async def get_briefing():
    return await BriefingService.get_briefing()
