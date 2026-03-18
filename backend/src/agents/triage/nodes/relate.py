"""Relate node — finds related tickets in the database by sender, category, and LLM semantic matching."""

import os
import logging

from pydantic import BaseModel, Field

from ....models import Message
from ....core.llm import get_llm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Structured output schema for cross-sender matching
# ---------------------------------------------------------------------------

class CrossSenderMatch(BaseModel):
    matched_message_id: str | None = Field(
        default=None,
        description="ID of the existing message that describes the same physical issue, or null if no match.",
    )
    confidence: str = Field(
        description="How confident: 'high', 'medium', or 'none'.",
    )
    reasoning: str = Field(
        description="One sentence: why these do or don't describe the same issue.",
    )


# ---------------------------------------------------------------------------
# LLM cross-sender matching
# ---------------------------------------------------------------------------

_CROSS_SENDER_SYSTEM = """You match property management messages that describe the SAME physical issue.

"Same physical issue" means:
- Same type of problem (e.g., both about a water leak)
- Same location in the building (e.g., both on the 3rd floor, both in the stairwell)

DIFFERENT locations are NOT the same issue, even if the problem type matches.
Example: a leak on the 3rd floor and flooding in the basement are SEPARATE issues.

Return the ID of the best matching message, or null if none match."""

_CROSS_SENDER_USER = """New message:
{new_content}

Existing messages (candidates):
{candidates}

Which candidate (if any) describes the same physical issue as the new message?
Return the candidate's ID, your confidence, and reasoning."""


async def _llm_cross_sender_match(
    content: str,
    candidates: list[Message],
    current_id: str,
) -> str | None:
    """Use LLM structured output to find a cross-sender match among candidates."""
    # Build candidate text (cap at 5, truncate content)
    candidate_lines = []
    for m in candidates[:5]:
        mid = str(m.id)
        if mid == current_id:
            continue
        candidate_lines.append(f"- ID: {mid} | Sender: {m.sender} | Content: {m.content[:200]}")

    if not candidate_lines:
        return None

    prompt = _CROSS_SENDER_USER.format(
        new_content=content[:300],
        candidates="\n".join(candidate_lines),
    )

    try:
        llm = get_llm(temperature=0.0).with_structured_output(CrossSenderMatch)
        result = llm.invoke(f"{_CROSS_SENDER_SYSTEM}\n\n{prompt}")

        if result.confidence == "high" and result.matched_message_id:
            # Validate that the returned ID is actually one of our candidates
            valid_ids = {str(m.id) for m in candidates}
            if result.matched_message_id in valid_ids:
                logger.info(
                    f"LLM cross-sender match: {result.matched_message_id} "
                    f"(confidence={result.confidence}, reason={result.reasoning})"
                )
                return result.matched_message_id
            else:
                logger.warning(f"LLM returned invalid ID: {result.matched_message_id}")

    except Exception as e:
        logger.warning(f"LLM cross-sender matching failed, skipping: {e}")

    return None


# ---------------------------------------------------------------------------
# Main relate node
# ---------------------------------------------------------------------------

async def relate(state: dict) -> dict:
    """Search for related messages from the same sender, same category, or similar content."""
    sender = state["sender"]
    category = state["category"]
    content = state["content"]
    current_id = state["message_id"]

    # Find recent messages from the same sender
    sender_messages = await Message.find(
        Message.sender == sender,
    ).to_list()

    # Find messages in the same category (if any have been classified)
    category_messages = []
    if category:
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

    # Determine primary group ID
    # Priority 1: same sender — group under oldest same-sender ticket
    primary_group_id = sender_related_ids[0] if sender_related_ids else None

    # Priority 2: cross-sender LLM matching within same category
    if not primary_group_id and category_messages and os.environ.get("OPENAI_API_KEY"):
        # Only consider candidates from different senders
        cross_sender_candidates = [
            m for m in category_messages
            if str(m.id) != current_id and m.sender != sender
        ]
        if cross_sender_candidates:
            matched_id = await _llm_cross_sender_match(content, cross_sender_candidates, current_id)
            if matched_id:
                # Group under the matched message's group_with root, or itself
                matched_msg = next((m for m in cross_sender_candidates if str(m.id) == matched_id), None)
                if matched_msg:
                    primary_group_id = matched_msg.group_with or matched_id
                    logger.info(
                        f"Cross-sender content match: message {current_id} grouped with {primary_group_id}"
                    )

    return {
        "related_ticket_ids": related_ids,
        "related_context": context,
        "group_with": primary_group_id,
    }
