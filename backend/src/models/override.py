"""
Triage overrides — manager corrections that become few-shot examples.

When a manager changes priority, category, or action on a triaged message,
the original and corrected values are stored here. These are later injected
as few-shot examples into the classify prompt so the LLM learns from corrections.
"""

from beanie import Document
from pydantic import Field
from typing import Optional
from datetime import datetime, timezone


class TriageOverride(Document):
    message_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # The message context (for few-shot reconstruction)
    sender: str
    channel: str
    content: str
    followup_count: int = 0

    # What the agent predicted
    original_priority: str
    original_category: Optional[str] = None
    original_action: Optional[str] = None

    # What the manager corrected it to
    corrected_priority: Optional[str] = None
    corrected_category: Optional[str] = None
    corrected_action: Optional[str] = None

    # Manager's reasoning (optional — shown in UI, useful for debugging)
    reason: Optional[str] = None

    class Settings:
        name = "triage_overrides"
