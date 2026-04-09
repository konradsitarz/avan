"""
Triage service — orchestrates the triage agent and falls back to regex
when no OPENAI_API_KEY is set.
"""

import os
import re
import logging

from ..models.message import Message, Priority, SenderType, TriageAction
from ..agents import run_triage

logger = logging.getLogger(__name__)


async def triage_message(message: Message) -> Message:
    """
    Run the full triage agent on a message.
    Populates priority, category, sender_type, triage_action, action_reason,
    related_ticket_ids, and draft_response on the message.
    Falls back to regex-based priority classification if no API key.
    """
    if os.environ.get("OPENAI_API_KEY"):
        try:
            result = await run_triage(
                message_id=str(message.id) if message.id else "",
                sender=message.sender,
                content=message.content,
                channel=message.type.value,
                followup_count=message.followup_count,
            )

            message.priority = Priority(result["priority"])
            message.category = result["category"]
            message.urgency = result["urgency"]
            message.importance = result["importance"]
            message.sender_type = SenderType(result["sender_type"])
            message.related_ticket_ids = result["related_ticket_ids"]
            message.group_with = result["group_with"]
            message.triage_action = TriageAction(result["action"])
            message.action_reason = result["action_reason"]
            message.draft_response = result["draft"]
            return message
        except Exception as e:
            logger.warning(f"Triage agent failed, falling back to regex: {e}")

    # Fallback: regex-based priority only
    message.priority = classify_priority(message.content, message.followup_count)
    return message


# ---------------------------------------------------------------------------
# Regex fallback (kept for environments without LLM access)
# ---------------------------------------------------------------------------

URGENT_PATTERNS = [
    r"building authority", r"electrical panel", r"hazard",
    r"fire", r"gas leak", r"evacuat", r"water.*centimeter",
    r"dangerous", r"unsafe",
    r"reporting this", r"lawyer", r"court", r"third time", r"THIRD TIME",
    r"nothing has been done", r"no response.*no response",
]

HIGH_PATTERNS = [
    r"gate.*open", r"elevator.*broken", r"leak", r"flooded ceiling",
    r"dripping", r"water in.*basement", r"smell", r"breakdown", r"broken",
    r"airbnb", r"building rules", r"violat",
    r"complaint.*noise", r"loud music", r"every night", r"fourth complaint",
    r"urgent", r"as soon as possible", r"expir", r"before.*meeting",
    r"again", r"third time", r"another time", r"not respond",
    r"gas install", r"electric", r"unintelligible",
]

LOW_PATTERNS = [
    r"invoice", r"statement", r"parking", r"payment",
    r"confirm", r"intercom", r"quick question", r"moved in",
]


def classify_priority(content: str, followup_count: int = 0) -> Priority:
    if followup_count >= 3:
        return Priority.URGENT

    text = content.lower()

    for pattern in URGENT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return Priority.URGENT

    high_hits = sum(1 for p in HIGH_PATTERNS if re.search(p, text, re.IGNORECASE))
    if high_hits >= 3:
        return Priority.URGENT
    if high_hits >= 1:
        return Priority.HIGH

    for pattern in LOW_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return Priority.LOW

    if followup_count >= 1:
        return Priority.HIGH

    return Priority.MEDIUM
