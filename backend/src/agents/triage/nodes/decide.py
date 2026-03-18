"""Decide node — determines the triage action: escalate, group, or standard."""

# Categories that represent direct hazards
_HAZARD_CATEGORIES = {"safety", "electrical", "compliance", "plumbing"}

# Polish-friendly reason fragments by category
_CATEGORY_REASONS = {
    "safety": "zagrożenie bezpieczeństwa — wymaga natychmiastowej reakcji",
    "plumbing": "awaria hydrauliczna — ryzyko zalania i szkód materialnych",
    "electrical": "problem elektryczny — ryzyko porażenia lub pożaru",
    "compliance": "kwestia zgodności/regulacji — ryzyko prawne",
    "noise": "uciążliwość hałasowa",
    "maintenance": "sprawa konserwacyjna",
    "billing": "kwestia rozliczeniowa",
    "access": "problem z dostępem",
    "other": "sprawa ogólna",
}


def _build_reason(category: str, priority: str, urgency: str, importance: str, followup_count: int) -> str:
    """Build a human-readable, context-aware triage reason in Polish."""
    cat_desc = _CATEGORY_REASONS.get(category, category)

    # Followup escalation — this is the primary reason, regardless of category
    if followup_count >= 3:
        return f"Lokator zgłaszał się już {followup_count} razy — eskalacja. Kategoria: {cat_desc}."

    # Hazard categories with urgent priority
    if category in _HAZARD_CATEGORIES and priority == "urgent":
        return f"Pilne: {cat_desc}."

    # Hazard categories at non-urgent priority (auto-escalated by category rule)
    if category in _HAZARD_CATEGORIES:
        return f"Kategoria ryzyka: {cat_desc} — eskalacja mimo priorytetu '{priority}'."

    # Urgent priority for non-hazard categories — explain using urgency/importance
    if priority == "urgent":
        if urgency == "immediate":
            return f"Sytuacja aktywna ({cat_desc}) — wymaga natychmiastowego działania."
        return f"Pilny priorytet ({cat_desc}) — eskalacja do zarządcy."

    # Standard/group — shouldn't normally reach here for escalations
    return f"{cat_desc.capitalize()}, priorytet {priority}."


def decide(state: dict) -> dict:
    """
    Rule-based decision with LLM-provided inputs.

    - escalate: urgent priority, safety category, or 3+ follow-ups
    - group: related tickets exist from the same sender → assign to primary ticket
    - standard: everything else
    """
    priority = state["priority"]
    category = state["category"]
    followup_count = state["followup_count"]
    urgency = state.get("urgency", "")
    importance = state.get("importance", "")
    related_ids = state["related_ticket_ids"]
    sender_type = state["sender_type"]
    group_with = state.get("group_with")

    # Escalation rules
    if priority == "urgent":
        return {
            "action": "escalate",
            "action_reason": _build_reason(category, priority, urgency, importance, followup_count),
            "group_with": group_with,
        }

    if category in _HAZARD_CATEGORIES:
        return {
            "action": "escalate",
            "action_reason": _build_reason(category, priority, urgency, importance, followup_count),
            "group_with": group_with,
        }

    if followup_count >= 3:
        return {
            "action": "escalate",
            "action_reason": _build_reason(category, priority, urgency, importance, followup_count),
            "group_with": group_with,
        }

    # Grouping rules — same sender has related open tickets
    if group_with and len(related_ids) >= 1:
        return {
            "action": "group",
            "action_reason": f"Zgrupowano z istniejącym zgłoszeniem {group_with} — ten sam nadawca, powiązana sprawa.",
            "group_with": group_with,
        }

    # Standard
    reason = _build_reason(category, priority, urgency, importance, followup_count)
    if sender_type == "vendor":
        reason += " Komunikacja od dostawcy — przekierować do działu zamówień."
    return {
        "action": "standard",
        "action_reason": reason,
        "group_with": None,
    }
