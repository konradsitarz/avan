"""
Triage service — orchestrates the triage agent and falls back to regex
when no OPENAI_API_KEY is set.
"""

import os
import re
import logging

from ..models.message import Message, Priority
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
            message.sender_type = result["sender_type"]
            message.related_ticket_ids = result["related_ticket_ids"]
            message.group_with = result["group_with"]
            message.triage_action = result["action"]
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
    r"nadzór budowlan", r"skrzynk[aę] elektryczn", r"zagrożeni[ae]",
    r"pożar", r"gaz[u ]", r"ewakuacj", r"wod[ay] na .* centymetr",
    r"groźn[ey]", r"niebezpiecz",
    r"zgłaszam sprawę", r"prawnik", r"sąd[u ]", r"po raz trzeci", r"PO RAZ TRZECI",
    r"nic nie zostało zrobione", r"brak odpowiedzi.*brak odpowiedzi",
]

HIGH_PATTERNS = [
    r"brama.*otwart[a]", r"winda.*zepsut[a]", r"przeciek", r"zalany? sufit",
    r"leje się", r"wod[ay] w piwnicy", r"śmierdzi", r"awari[aę]", r"zepsut[aey]",
    r"airbnb", r"regulamin", r"niezgodn[eay]",
    r"skarg[iae].*hałas", r"głośn[aey] muzyk", r"każd[aąey] noc", r"czwart[aey] skarg",
    r"pilne", r"jak najszybciej", r"kończy się", r"przed.*zebraniem",
    r"ponownie", r"znowu", r"trzeci raz", r"kolejny raz", r"nie odpowiada",
    r"instal.*gazow", r"elektryk", r"nieczytelne",
]

LOW_PATTERNS = [
    r"faktur[aęy]", r"rozliczeni[ae]", r"parking", r"wpłat[aęy]",
    r"potwierdzi[ćę]", r"intercom", r"domofon", r"quick question", r"moved in",
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
