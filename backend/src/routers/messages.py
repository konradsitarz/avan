from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
from beanie import PydanticObjectId

from ..models import Message, Briefing, TriageOverride
from ..services import BriefingService, triage_message


class OverrideRequest(BaseModel):
    priority: Optional[str] = None
    category: Optional[str] = None
    action: Optional[str] = None
    reason: Optional[str] = None

router = APIRouter(prefix="/api/messages", tags=["messages"])

@router.get("", response_model=List[Message])
async def get_messages():
    messages = await Message.find_all().to_list()
    return messages

@router.post("", response_model=Message)
async def create_message(message: Message):
    # Save first so the message always enters the system, even if triage fails
    await message.insert()
    try:
        message = await triage_message(message)
        await message.save()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Triage failed for {message.id}, message saved without triage: {e}")
    await BriefingService.invalidate()
    return message

@router.get("/{message_id}", response_model=Message)
async def get_message(message_id: str):
    message = await Message.get(PydanticObjectId(message_id))
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return message

@router.post("/{message_id}/override", response_model=Message)
async def override_triage(message_id: str, override: OverrideRequest):
    """Manager overrides triage decision — stored as few-shot example for future classification."""
    message = await Message.get(PydanticObjectId(message_id))
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    # Record the override as a few-shot example
    has_change = False
    update_fields = {}

    triage_override = TriageOverride(
        message_id=message_id,
        sender=message.sender,
        channel=message.type.value,
        content=message.content,
        followup_count=message.followup_count,
        original_priority=message.priority.value,
        original_category=message.category,
        original_action=message.triage_action.value if message.triage_action else None,
        reason=override.reason,
    )

    if override.priority and override.priority != message.priority.value:
        triage_override.corrected_priority = override.priority
        update_fields[Message.priority] = override.priority
        has_change = True

    if override.category and override.category != message.category:
        triage_override.corrected_category = override.category
        update_fields[Message.category] = override.category
        has_change = True

    if override.action and override.action != (message.triage_action.value if message.triage_action else None):
        triage_override.corrected_action = override.action
        update_fields[Message.triage_action] = override.action
        has_change = True

    if has_change:
        await triage_override.insert()
        if update_fields:
            await message.set(update_fields)
        await BriefingService.invalidate()

    return await Message.get(PydanticObjectId(message_id))


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
    """Clear all messages, briefings, and overrides — for simulation resets."""
    await Message.delete_all()
    await Briefing.delete_all()
    await TriageOverride.delete_all()
    return {"message": "All messages, briefings, and overrides cleared"}


@router.delete("/{message_id}")
async def delete_message(message_id: str):
    message = await Message.get(PydanticObjectId(message_id))
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    await message.delete()
    await BriefingService.invalidate()
    return {"message": "Deleted successfully"}
