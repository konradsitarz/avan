"""Relate node — finds related tickets in the database by sender and category."""

import logging

from ....models import Message

logger = logging.getLogger(__name__)


async def relate(state: dict) -> dict:
    """Search for related messages from the same sender or same category."""
    sender = state["sender"]
    category = state["category"]
    current_id = state["message_id"]

    # Find recent messages from the same sender
    sender_messages = await Message.find(
        Message.sender == sender,
    ).to_list()

    # Find messages in the same category (if any have been classified)
    category_messages = await Message.find(
        Message.category == category,
    ).to_list()

    # Deduplicate and exclude current message
    seen = set()
    related = []
    sender_related_ids = []
    for m in sender_messages:
        mid = str(m.id)
        if mid != current_id and mid not in seen:
            seen.add(mid)
            related.append(m)
            sender_related_ids.append(mid)

    for m in category_messages:
        mid = str(m.id)
        if mid != current_id and mid not in seen:
            seen.add(mid)
            related.append(m)

    related_ids = [str(m.id) for m in related[:10]]

    # Build context summary for downstream nodes
    if related:
        lines = []
        for m in related[:5]:
            lines.append(
                f"- [{m.priority.value.upper()}] {m.sender} ({m.type.value}): "
                f"{m.content[:100]}{'...' if len(m.content) > 100 else ''}"
            )
        context = f"{len(related)} related ticket(s) found:\n" + "\n".join(lines)
    else:
        context = "No related tickets found."

    # Pick the oldest same-sender ticket as the primary to group under
    primary_group_id = sender_related_ids[0] if sender_related_ids else None

    return {
        "related_ticket_ids": related_ids,
        "related_context": context,
        "group_with": primary_group_id,
    }
