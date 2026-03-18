from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone
from enum import Enum

class MessageType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    VOICE = "voice"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class SenderType(str, Enum):
    RESIDENT = "resident"
    VENDOR = "vendor"
    SYSTEM = "system"

class TriageAction(str, Enum):
    ESCALATE = "escalate"
    GROUP = "group"
    STANDARD = "standard"

class Message(Document):
    type: MessageType
    sender: str
    content: str
    priority: Priority = Priority.MEDIUM
    followup_count: int = 0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    assigned_to: Optional[str] = None

    # Triage agent output
    category: Optional[str] = None
    sender_type: Optional[SenderType] = None
    related_ticket_ids: list[str] = Field(default_factory=list)
    group_with: Optional[str] = None  # ID of the primary ticket this is grouped under
    triage_action: Optional[TriageAction] = None
    action_reason: Optional[str] = None
    draft_response: Optional[str] = None

    class Settings:
        name = "messages"
