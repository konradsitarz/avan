from fastapi import APIRouter, HTTPException
from typing import List
from beanie import PydanticObjectId

from ..models import Message, Briefing
from ..services import BriefingService, triage_message

router = APIRouter(prefix="/api/messages", tags=["messages"])

@router.get("", response_model=List[Message])
async def get_messages():
    messages = await Message.find_all().to_list()
    return messages

@router.post("", response_model=Message)
async def create_message(message: Message):
    message = await triage_message(message)
    await message.insert()
    await BriefingService.invalidate()
    return message

@router.get("/{message_id}", response_model=Message)
async def get_message(message_id: str):
    message = await Message.get(PydanticObjectId(message_id))
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.put("/{message_id}", response_model=Message)
async def update_message(message_id: str, updated_data: Message):
    message = await Message.get(PydanticObjectId(message_id))
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    await message.set({
        Message.type: updated_data.type,
        Message.sender: updated_data.sender,
        Message.content: updated_data.content,
        Message.priority: updated_data.priority,
        Message.followup_count: updated_data.followup_count,
        Message.assigned_to: updated_data.assigned_to,
    })

    await BriefingService.invalidate()
    return message

@router.delete("/all")
async def delete_all_messages():
    """Clear all messages and cached briefings — for simulation resets."""
    await Message.delete_all()
    await Briefing.delete_all()
    return {"message": "All messages and briefings cleared"}


@router.delete("/{message_id}")
async def delete_message(message_id: str):
    message = await Message.get(PydanticObjectId(message_id))
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    await message.delete()
    await BriefingService.invalidate()
    return {"message": "Deleted successfully"}
