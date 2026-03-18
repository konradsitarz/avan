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
    unassigned_note: str  # Only populated when some messages are assigned (otherwise empty)
    briefing_summary: str
    issue_briefs: list[dict]


SYSTEM_PROMPT = """Jesteś profesjonalnym asystentem concierge do zarządzania nieruchomościami.
Mówisz ciepłym, ale rzeczowym tonem — jak zaufany doradca, który briefuje zapracowanego zarządcę
przy porannej kawie. Bądź bezpośredni, ludzki i konkretny.

Zarządzasz nieruchomościami mieszkalnymi w Polsce.
Wiadomości od lokatorów są najczęściej po polsku — rozumiesz polski biegle
i zawsze piszesz briefingi po polsku.

Nigdy nie używaj punktów ani list w podsumowaniu. Pisz płynną prozą, maksymalnie 2-3 zdania.
Skup się na tym, co najważniejsze i ogólnej sytuacji."""

SUMMARY_PROMPT = """Oto aktualne aktywne sprawy na Twoich nieruchomościach:

{messages_text}

Statystyki: {message_count} spraw łącznie, {urgent_count} pilnych, {high_count} o wysokim priorytecie.{unassigned_note}

Napisz 2-3 zdaniowy briefing dla zarządcy nieruchomości. Bądź ciepły, ale bezpośredni.
Zacznij od najważniejszej sytuacji, potem daj ogólny obraz obciążenia.
NIE wymieniaj poszczególnych spraw — namaluj ogólny obraz."""

ISSUE_PROMPT = """Briefujesz zarządcę nieruchomości na temat tej sprawy.

Nadawca: {sender}
Kategoria: {category}
Ogólny priorytet: {priority}
Przypisano do: {assigned_to}

Oś czasu wiadomości (od najstarszej):
{timeline}

Napisz 2-3 zdaniowy brief w stylu concierge o tej sprawie. Wyjaśnij:
1. Co się dzieje (podsumuj cały wątek, nie tylko ostatnią wiadomość)
2. Jak sprawa eskalowała w czasie (jeśli jest wiele wiadomości)
3. Co zarządca powinien zrobić dalej

Bądź ludzki i bezpośredni. Pisz po polsku.
Nie powtarzaj metadanych — skup się na sytuacji, pilności i zalecanym działaniu."""


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
        unassigned_note=state["unassigned_note"],
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

        # Build timeline text from all messages in this issue thread
        timeline_entries = issue.get("timeline", [])
        if timeline_entries:
            timeline_text = "\n".join(
                f"  [{entry['time_label']}] via {entry['type']}: {entry['content'][:300]}"
                for entry in timeline_entries
            )
        else:
            timeline_text = f"  [{issue['time_label']}] via {issue['type']}: {issue['content'][:300]}"

        prompt = ISSUE_PROMPT.format(
            sender=issue["sender"],
            category=issue.get("category") or "bez kategorii",
            priority=issue["priority"],
            assigned_to=issue.get("assigned_to") or "Nikt (nieprzypisane)",
            timeline=timeline_text,
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

# Categories representing direct life/safety threats — sort above other urgent issues
_LIFE_THREAT_CATEGORIES = {"safety", "plumbing", "electrical"}

# Eisenhower sorting: urgency (can it wait?) × importance (how serious?)
_URGENCY_ORDER = {"immediate": 0, "today": 1, "this_week": 2, "no_rush": 3}
_IMPORTANCE_ORDER = {"critical": 0, "high": 1, "moderate": 2, "low": 3}


def _eisenhower_quadrant(urgency: str | None, importance: str | None) -> str:
    """Map urgency × importance to an Eisenhower quadrant label."""
    is_urgent = (urgency or "this_week") in ("immediate", "today")
    is_important = (importance or "moderate") in ("critical", "high")
    if is_urgent and is_important:
        return "urgent_important"       # Do first
    if not is_urgent and is_important:
        return "not_urgent_important"   # Schedule
    if is_urgent and not is_important:
        return "urgent_not_important"   # Delegate
    return "not_urgent_not_important"   # Deprioritize


_QUADRANT_ORDER = {
    "urgent_important": 0,
    "urgent_not_important": 1,
    "not_urgent_important": 2,
    "not_urgent_not_important": 3,
}


class BriefingService:
    """Manages briefing generation and caching."""

    @staticmethod
    async def invalidate():
        """Mark the latest cached briefing as stale."""
        latest = await Briefing.find(
            Briefing.stale == False,  # noqa: E712
        ).sort("-generated_at").first_or_none()
        if latest:
            latest.stale = True
            await latest.save()

    @staticmethod
    async def get_briefing() -> dict:
        """Return cached briefing if fresh, otherwise regenerate."""
        cached = await Briefing.find(
            Briefing.stale == False,  # noqa: E712
        ).sort("-generated_at").first_or_none()
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
                "summary": "Dobra wiadomość — skrzynka jest pusta. Brak aktywnych spraw na Twoich nieruchomościach.",
                "issues": [],
                "stats": BriefingService._build_stats(messages),
            }
            await BriefingService._save(result, now)
            return result

        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        sorted_messages = sorted(
            messages, key=lambda m: (priority_order.get(m.priority.value, 99), m.created_at)
        )

        grouped_messages = BriefingService._group_messages(sorted_messages)
        items = [BriefingService._build_item(m, now, related) for m, related in grouped_messages]
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
            msg_count = item.get("message_count", 1)
            label = f"[{item['priority'].upper()}] {item.get('category', '?')} — {item['sender']}"
            if msg_count > 1:
                label += f" ({msg_count} wiadomości)"
            messages_text += f"{label}: {item['content'][:200]}\n"

        initial_state: BriefingState = {
            "messages_text": messages_text,
            "message_count": stats["total"],
            "urgent_count": stats["urgent"],
            "high_count": stats["high"],
            "unassigned_note": (
                f" {stats['unassigned']} nieprzypisanych."
                if stats["unassigned"] < stats["total"]
                else ""
            ),
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
    def _resolve_root(message_id: str, group_with_map: dict[str, str]) -> str:
        """Walk group_with chains to find the root primary ticket ID."""
        visited = set()
        current = message_id
        while current in group_with_map and current not in visited:
            visited.add(current)
            current = group_with_map[current]
        return current

    @staticmethod
    def _group_messages(messages: list[Message]) -> list[tuple[Message, list[Message]]]:
        """
        Group messages into issue threads using the triage agent's group_with
        field as the primary grouping key, with sender||category as fallback.

        Phase 1: Build a group_with map and resolve chains (A→B→C becomes A→C)
        Phase 2: Group messages by their resolved root ID
        Phase 3: For messages without group_with (self-primary), merge by
                 sender||category as fallback (handles regex fallback cases)
        """
        # Build lookup: message_id → message
        by_id: dict[str, Message] = {str(m.id): m for m in messages}

        # Build group_with map for chain resolution
        group_with_map: dict[str, str] = {}
        for m in messages:
            if m.group_with:
                group_with_map[str(m.id)] = m.group_with

        # Phase 1 & 2: group by resolved root
        root_groups: dict[str, list[Message]] = {}
        for m in messages:
            mid = str(m.id)
            if m.group_with:
                root = BriefingService._resolve_root(mid, group_with_map)
                root_groups.setdefault(root, []).append(m)
            else:
                # Self-primary — temporarily keyed by own ID
                root_groups.setdefault(mid, []).append(m)

        # Phase 3: merge self-primary groups by sender||category fallback
        merged: dict[str, list[Message]] = {}
        fallback_mapping: dict[str, str] = {}  # sender||category → first key seen

        for key, msgs in root_groups.items():
            # If this group was formed by group_with (key is a root ID that
            # some message points to), keep it as-is
            has_grouped_members = any(
                m.group_with and str(m.id) != key for m in msgs
            )
            if has_grouped_members or key not in by_id:
                # group_with-based group — keep under this key
                merged.setdefault(key, []).extend(msgs)
            else:
                # Self-primary group — merge by sender||category
                primary_msg = by_id[key]
                fb_key = f"{primary_msg.sender}||{primary_msg.category or 'uncategorized'}"
                if fb_key in fallback_mapping:
                    merged[fallback_mapping[fb_key]].extend(msgs)
                else:
                    fallback_mapping[fb_key] = key
                    merged.setdefault(key, []).extend(msgs)

        # Also merge any group_with group into an existing fallback group
        # if the root message itself is a self-primary in a fallback group
        # (This handles: root message is self-primary, other messages point to it)

        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        result = []

        for group_msgs in merged.values():
            # Deduplicate (a message could appear twice if it's both root and member)
            seen_ids = set()
            deduped = []
            for m in group_msgs:
                if str(m.id) not in seen_ids:
                    seen_ids.add(str(m.id))
                    deduped.append(m)

            # Sort by time (oldest first) for timeline
            deduped.sort(key=lambda m: m.created_at)
            # Primary = highest priority message (latest if tied)
            primary = max(
                deduped,
                key=lambda m: (-priority_order.get(m.priority.value, 99), m.created_at),
            )
            related = [m for m in deduped if m.id != primary.id]
            result.append((primary, related))

        # Sort groups: Eisenhower quadrant first, then life-threat categories, then priority, then time
        result.sort(key=lambda t: (
            _QUADRANT_ORDER.get(_eisenhower_quadrant(t[0].urgency, t[0].importance), 99),
            0 if t[0].category in _LIFE_THREAT_CATEGORIES else 1,
            priority_order.get(t[0].priority.value, 99),
            t[0].created_at,
        ))

        return result

    @staticmethod
    def _time_label(created_at: datetime, now: datetime) -> str:
        created = created_at.replace(tzinfo=timezone.utc) if created_at.tzinfo is None else created_at
        age = now - created
        if age < timedelta(hours=1):
            return "przed chwilą"
        elif age < timedelta(hours=2):
            return "około godziny temu"
        elif age < timedelta(hours=24):
            hours = int(age.total_seconds() / 3600)
            if hours < 5:
                return f"{hours} godziny temu"
            return f"{hours} godzin temu"
        elif age < timedelta(days=2):
            return "wczoraj"
        else:
            days = int(age.total_seconds() / 86400)
            if days < 5:
                return f"{days} dni temu"
            return f"{days} dni temu"

    @staticmethod
    def _build_item(m: Message, now: datetime, related: list[Message] | None = None) -> dict:
        # Build timeline: all messages in this issue thread, sorted oldest first
        all_messages = sorted(
            [m] + (related or []),
            key=lambda msg: msg.created_at,
        )

        timeline = []
        for msg in all_messages:
            timeline.append({
                "id": str(msg.id),
                "content": msg.content,
                "type": msg.type.value,
                "priority": msg.priority.value,
                "time_label": BriefingService._time_label(msg.created_at, now),
                "created_at": msg.created_at.isoformat(),
                "action_reason": msg.action_reason,
            })

        # Total follow-ups across the thread
        total_followups = sum(msg.followup_count for msg in all_messages)

        item = {
            "id": str(m.id),
            "sender": m.sender.strip(),
            "content": m.content,  # primary message content
            "priority": m.priority.value,
            "urgency": m.urgency,
            "importance": m.importance,
            "quadrant": _eisenhower_quadrant(m.urgency, m.importance),
            "type": m.type.value,
            "time_label": BriefingService._time_label(m.created_at, now),
            "created_at": m.created_at.isoformat(),
            "assigned_to": m.assigned_to,
            "followup_count": total_followups,
            "category": m.category,
            "action_reason": m.action_reason,
            "draft_response": m.draft_response,
            "llm_brief": None,
            "message_count": len(all_messages),
            "timeline": timeline,
        }

        return item

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
            return f"Masz {n} aktywnych spraw, z czego {urgent} jest pilnych i wymaga natychmiastowej uwagi. Żadna nie została jeszcze przypisana — priorytetem powinien być triaż krytycznych zgłoszeń."
        return f"Masz {n} aktywnych spraw na swoich nieruchomościach. Nic krytycznego w tej chwili, ale są sprawy wymagające uwagi dziś."
