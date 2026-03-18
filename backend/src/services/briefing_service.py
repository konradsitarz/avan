"""
Briefing service — owns caching and LLM-based briefing generation.

The briefing is stored in MongoDB and only regenerated when messages change
(i.e., when the cached briefing is marked stale or doesn't exist).
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from collections import Counter
from typing import TypedDict

from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

from ..models import Message, Priority, Briefing
from ..core.llm import get_llm

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# LangGraph agent state & prompts
# ---------------------------------------------------------------------------

class BriefingState(TypedDict):
    messages_text: str
    message_count: int
    urgent_count: int
    high_count: int
    unassigned_count: int
    briefing_summary: str
    issue_briefs: list[dict]


SYSTEM_PROMPT = """You are a professional property management concierge assistant.
You speak in a warm but efficient tone — like a trusted advisor briefing a busy manager
over morning coffee. Be direct, human, and actionable.

You are based in Eastern Central Europe and manage residential properties.
Messages from residents may be in Polish — you understand Polish fluently
but always write your briefings in English.

Never use bullet points or lists in the summary. Write in flowing prose, 2-3 sentences max.
Focus on what matters most and the overall situation."""

SUMMARY_PROMPT = """Here are the current active issues across your properties:

{messages_text}

Stats: {message_count} total issues, {urgent_count} urgent, {high_count} high priority, {unassigned_count} unassigned.

Write a 2-3 sentence executive briefing for the property manager. Be warm but direct.
Mention the most critical situation first, then give an overall sense of the workload.
Do NOT list individual issues — paint the big picture."""

ISSUE_PROMPT = """You are briefing a property manager about this specific issue:

From: {sender}
Channel: {channel}
Priority: {priority}
Follow-ups: {followup_count}
Received: {time_label}
Assigned to: {assigned_to}

Original message:
{content}

Write a 1-2 sentence concierge-style brief about this issue. Explain what's happening,
why it matters, and suggest the next step. Be human and direct. If the message is in Polish,
summarize it in English. Don't repeat metadata — focus on the situation and what to do."""


# ---------------------------------------------------------------------------
# LangGraph agent nodes
# ---------------------------------------------------------------------------

def generate_summary(state: BriefingState) -> dict:
    llm = get_llm(temperature=0.7)
    prompt = SUMMARY_PROMPT.format(
        messages_text=state["messages_text"],
        message_count=state["message_count"],
        urgent_count=state["urgent_count"],
        high_count=state["high_count"],
        unassigned_count=state["unassigned_count"],
    )
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])
    return {"briefing_summary": response.content}


def generate_issue_briefs(state: BriefingState) -> dict:
    llm = get_llm(temperature=0.7)
    briefs = []
    for issue in state["issue_briefs"]:
        if issue.get("llm_brief"):
            briefs.append(issue)
            continue

        prompt = ISSUE_PROMPT.format(
            sender=issue["sender"],
            channel=issue["type"],
            priority=issue["priority"],
            followup_count=issue["followup_count"],
            time_label=issue["time_label"],
            assigned_to=issue.get("assigned_to") or "Nobody (unassigned)",
            content=issue["content"],
        )
        response = llm.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ])
        issue["llm_brief"] = response.content
        briefs.append(issue)

    return {"issue_briefs": briefs}


# Compile the graph once at module level
_workflow = StateGraph(BriefingState)
_workflow.add_node("generate_summary", generate_summary)
_workflow.add_node("generate_issue_briefs", generate_issue_briefs)
_workflow.set_entry_point("generate_summary")
_workflow.add_edge("generate_summary", "generate_issue_briefs")
_workflow.add_edge("generate_issue_briefs", END)
_briefing_graph = _workflow.compile()


# ---------------------------------------------------------------------------
# Service class
# ---------------------------------------------------------------------------

class BriefingService:
    """Manages briefing generation and caching."""

    @staticmethod
    async def invalidate():
        """Mark the latest cached briefing as stale."""
        latest = await Briefing.find_one(sort_expression=[("-generated_at", -1)])
        if latest and not latest.stale:
            latest.stale = True
            await latest.save()

    @staticmethod
    async def get_briefing() -> dict:
        """Return cached briefing if fresh, otherwise regenerate."""
        cached = await Briefing.find_one(
            Briefing.stale == False,  # noqa: E712
            sort_expression=[("-generated_at", -1)],
        )
        if cached:
            return {
                "generated_at": cached.generated_at.isoformat(),
                "summary": cached.summary,
                "issues": cached.issues,
                "stats": cached.stats,
            }

        # Generate fresh briefing
        return await BriefingService._generate_and_store()

    @staticmethod
    async def _generate_and_store() -> dict:
        messages = await Message.find_all().to_list()
        now = datetime.now(timezone.utc)

        if not messages:
            result = {
                "generated_at": now.isoformat(),
                "summary": "Good news — your inbox is clear. No active issues to report across your properties.",
                "issues": [],
                "stats": BriefingService._build_stats(messages),
            }
            await BriefingService._save(result, now)
            return result

        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        sorted_messages = sorted(
            messages, key=lambda m: (priority_order.get(m.priority.value, 99), m.created_at)
        )

        items = [BriefingService._build_item(m, now) for m in sorted_messages]
        stats = BriefingService._build_stats(messages)

        # Try LLM generation
        if os.environ.get("OPENAI_API_KEY"):
            try:
                llm_result = await BriefingService._run_agent(items, stats)
                result = {
                    "generated_at": now.isoformat(),
                    "summary": llm_result["summary"],
                    "issues": llm_result["issues"],
                    "stats": stats,
                }
                await BriefingService._save(result, now)
                return result
            except Exception as e:
                logger.warning(f"LLM briefing failed, using fallback: {e}")

        # Fallback
        result = {
            "generated_at": now.isoformat(),
            "summary": BriefingService._fallback_summary(messages, stats),
            "issues": items,
            "stats": stats,
        }
        await BriefingService._save(result, now)
        return result

    @staticmethod
    async def _run_agent(items: list, stats: dict) -> dict:
        """Run the LangGraph briefing agent."""
        messages_text = ""
        for item in items:
            messages_text += (
                f"[{item['priority'].upper()}] From {item['sender']} via {item['type']} "
                f"({item['time_label']}): {item['content'][:200]}\n"
            )

        initial_state: BriefingState = {
            "messages_text": messages_text,
            "message_count": stats["total"],
            "urgent_count": stats["urgent"],
            "high_count": stats["high"],
            "unassigned_count": stats["unassigned"],
            "briefing_summary": "",
            "issue_briefs": [dict(item) for item in items],
        }

        result = await _briefing_graph.ainvoke(initial_state)
        return {
            "summary": result["briefing_summary"],
            "issues": result["issue_briefs"],
        }

    @staticmethod
    async def _save(result: dict, generated_at: datetime):
        """Persist the briefing to MongoDB."""
        briefing = Briefing(
            generated_at=generated_at,
            summary=result["summary"],
            issues=result["issues"],
            stats=result["stats"],
            stale=False,
        )
        await briefing.insert()

    @staticmethod
    def _build_item(m: Message, now: datetime) -> dict:
        age = now - m.created_at
        if age < timedelta(hours=1):
            time_label = "just now"
        elif age < timedelta(hours=2):
            time_label = "about an hour ago"
        elif age < timedelta(hours=24):
            time_label = f"{int(age.total_seconds() / 3600)} hours ago"
        elif age < timedelta(days=2):
            time_label = "yesterday"
        else:
            time_label = f"{int(age.total_seconds() / 86400)} days ago"

        return {
            "id": str(m.id),
            "sender": m.sender.strip(),
            "content": m.content,
            "priority": m.priority.value,
            "type": m.type.value,
            "time_label": time_label,
            "created_at": m.created_at.isoformat(),
            "assigned_to": m.assigned_to,
            "followup_count": m.followup_count,
            "llm_brief": None,
        }

    @staticmethod
    def _build_stats(messages: list) -> dict:
        channels = Counter(m.type.value for m in messages)
        sender_counts = Counter(m.sender for m in messages)
        return {
            "total": len(messages),
            "urgent": sum(1 for m in messages if m.priority == Priority.URGENT),
            "high": sum(1 for m in messages if m.priority == Priority.HIGH),
            "medium": sum(1 for m in messages if m.priority == Priority.MEDIUM),
            "low": sum(1 for m in messages if m.priority == Priority.LOW),
            "unassigned": sum(1 for m in messages if not m.assigned_to),
            "channels": dict(channels),
            "top_senders": [{"sender": s, "count": c} for s, c in sender_counts.most_common(5)],
        }

    @staticmethod
    def _fallback_summary(messages, stats):
        n = len(messages)
        urgent = stats["urgent"]
        if urgent > 0:
            return f"You have {n} active issues, {urgent} of which are urgent and need immediate attention. None of these have been assigned yet — your first priority should be triaging the critical ones."
        return f"You have {n} active issues across your properties. Nothing critical right now, but there are items that need attention today."
