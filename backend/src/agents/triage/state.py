from typing import TypedDict


class TriageState(TypedDict):
    # Input
    message_id: str
    sender: str
    content: str
    channel: str           # email / sms / voice
    followup_count: int

    # Classify node output
    category: str           # e.g. "plumbing", "noise", "billing", "safety", "maintenance"
    priority: str           # low / medium / high / urgent
    sender_type: str        # resident / vendor / system

    # Relate node output
    related_ticket_ids: list[str]
    related_context: str    # summary of related tickets for downstream nodes

    # Decide node output
    action: str             # escalate / group / standard
    action_reason: str      # human-readable explanation shown in UI
    group_with: str | None  # ID of the primary ticket this groups under

    # Draft node output
    draft: str | None
    draft_channel: str      # sms / email
