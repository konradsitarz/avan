"""
Few-shot example loader for the triage classify node.

Fetches recent manager overrides from the DB and formats them as
examples that get injected into the classify prompt.
"""

from ...models.override import TriageOverride

MAX_EXAMPLES = 5


async def load_few_shot_examples() -> str:
    """
    Load the most recent triage overrides and format them as few-shot examples.
    Returns empty string if no overrides exist.
    """
    overrides = await TriageOverride.find().sort("-created_at").limit(MAX_EXAMPLES).to_list()

    if not overrides:
        return ""

    lines = ["Here are examples of how the property manager has corrected previous classifications. Learn from these:\n"]

    for o in overrides:
        lines.append(f"Message from {o.sender} via {o.channel}: \"{o.content[:200]}\"")

        corrections = []
        if o.corrected_priority and o.corrected_priority != o.original_priority:
            corrections.append(f"priority {o.original_priority} -> {o.corrected_priority}")
        if o.corrected_category and o.corrected_category != o.original_category:
            corrections.append(f"category {o.original_category} -> {o.corrected_category}")

        if corrections:
            lines.append(f"  Correction: {', '.join(corrections)}")
        if o.reason:
            lines.append(f"  Reason: {o.reason}")
        lines.append("")

    return "\n".join(lines)
