"""Decide node — determines the triage action: escalate, group, or standard."""


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
    related_ids = state["related_ticket_ids"]
    sender_type = state["sender_type"]
    group_with = state.get("group_with")

    # Escalation rules
    if priority == "urgent":
        return {
            "action": "escalate",
            "action_reason": f"Urgent priority — {category} issue requires immediate admin attention.",
            "group_with": group_with,
        }

    if category in ("safety", "electrical", "compliance", "plumbing"):
        return {
            "action": "escalate",
            "action_reason": f"{category.capitalize()} issue — potential hazard, flagged for immediate review.",
            "group_with": group_with,
        }

    if followup_count >= 3:
        return {
            "action": "escalate",
            "action_reason": f"Resident has followed up {followup_count} times — escalating to prevent churn.",
            "group_with": group_with,
        }

    # Grouping rules — same sender has related open tickets
    if group_with and len(related_ids) >= 1:
        return {
            "action": "group",
            "action_reason": f"Grouped with existing ticket {group_with} — same sender, likely related issue.",
            "group_with": group_with,
        }

    # Standard
    reason = f"{category.capitalize()} issue, {priority} priority"
    if sender_type == "vendor":
        reason += " — vendor communication, route to procurement."
    return {
        "action": "standard",
        "action_reason": reason,
        "group_with": None,
    }
