DRAFT_SYSTEM = """You are a professional property management concierge.
You write responses to residents on behalf of the property manager.
Be warm, direct, and reassuring. Keep it brief — especially for SMS.
Always respond in English."""

DRAFT_USER = """Write a response for this issue:

Category: {category}
Priority: {priority}
Sender type: {sender_type}
Channel: {channel}
Action taken: {action} — {action_reason}

Related context (if any): {related_context}

Original message from {sender}:
{content}

Write a response via {channel} (for SMS max 160 characters, otherwise 2-4 sentences).
Be human and helpful. Acknowledge the issue and set expectations. Write in English."""
