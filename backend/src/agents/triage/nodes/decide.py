"""Decide node — determines the triage action: escalate, group, or standard."""

# Categories that represent direct hazards
_HAZARD_CATEGORIES = {"safety", "electrical", "compliance", "plumbing"}

# Reason fragments by category
_CATEGORY_REASONS = {
    "safety": "safety hazard — requires immediate attention",
    "plumbing": "plumbing emergency — risk of flooding and property damage",
    "electrical": "electrical issue — risk of shock or fire",
    "compliance": "compliance/regulatory issue — legal risk",
    "noise": "noise disturbance",
    "maintenance": "maintenance issue",
    "billing": "billing matter",
    "access": "access problem",
    "other": "general issue",
}


def _build_reason(category: str, priority: str, urgency: str, importance: str, followup_count: int) -> str:
    """Build a human-readable, context-aware triage reason."""
    cat_desc = _CATEGORY_REASONS.get(category, category)

    # Followup escalation — this is the primary reason, regardless of category
    if followup_count >= 3:
        return f"Resident has followed up {followup_count} times — escalating. Category: {cat_desc}."

    # Hazard categories with urgent priority
    if category in _HAZARD_CATEGORIES and priority == "urgent":
        return f"Urgent: {cat_desc}."

    # Hazard categories at non-urgent priority (auto-escalated by category rule)
    if category in _HAZARD_CATEGORIES:
        return f"Risk category: {cat_desc} — escalating despite '{priority}' priority."

    # Urgent priority for non-hazard categories — explain using urgency/importance
    if priority == "urgent":
        if urgency == "immediate":
            return f"Active situation ({cat_desc}) — requires immediate action."
        return f"Urgent priority ({cat_desc}) — escalating to manager."

    # Standard/group — shouldn't normally reach here for escalations
    return f"{cat_desc.capitalize()}, priority {priority}."


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
            "action_reason": f"Grouped with existing ticket {group_with} — same sender, related issue.",
            "group_with": group_with,
        }

    # Standard
    reason = _build_reason(category, priority, urgency, importance, followup_count)
    if sender_type == "vendor":
        reason += " Vendor communication — route to procurement."
    return {
        "action": "standard",
        "action_reason": reason,
        "group_with": None,
    }
