"""Draft node — generates a channel-appropriate response via LLM."""

from langchain_core.messages import SystemMessage, HumanMessage

from ....core.llm import get_llm
from ..prompts.draft import DRAFT_SYSTEM, DRAFT_USER


def draft(state: dict) -> dict:
    """Generate a draft response. Skipped for escalations (admin decides)."""
    if state["action"] == "escalate":
        return {"draft": None, "draft_channel": state["channel"]}

    llm = get_llm(temperature=0.7)

    prompt = DRAFT_USER.format(
        category=state["category"],
        priority=state["priority"],
        sender_type=state["sender_type"],
        channel=state["channel"],
        action=state["action"],
        action_reason=state["action_reason"],
        related_context=state["related_context"],
        sender=state["sender"],
        content=state["content"],
    )

    response = llm.invoke([
        SystemMessage(content=DRAFT_SYSTEM),
        HumanMessage(content=prompt),
    ])

    return {
        "draft": response.content,
        "draft_channel": state["channel"],
    }
