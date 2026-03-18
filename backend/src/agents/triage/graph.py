"""
Triage agent LangGraph — the full flow:

    classify → relate → decide
                          ├── escalate  → END (no draft, admin decides)
                          ├── group     → draft → END
                          └── standard  → draft → END
"""

from langgraph.graph import StateGraph, END

from .state import TriageState
from .nodes import classify, relate, decide, draft


def _route_after_decide(state: TriageState) -> str:
    """Conditional edge: skip draft for escalations."""
    if state["action"] == "escalate":
        return "end"
    return "draft"


# Build graph
_workflow = StateGraph(TriageState)

_workflow.add_node("classify", classify)
_workflow.add_node("relate", relate)
_workflow.add_node("decide", decide)
_workflow.add_node("draft", draft)

_workflow.set_entry_point("classify")
_workflow.add_edge("classify", "relate")
_workflow.add_edge("relate", "decide")
_workflow.add_conditional_edges("decide", _route_after_decide, {
    "draft": "draft",
    "end": END,
})
_workflow.add_edge("draft", END)

triage_graph = _workflow.compile()


async def run_triage(
    message_id: str,
    sender: str,
    content: str,
    channel: str,
    followup_count: int,
) -> TriageState:
    """Run the triage agent and return the full state."""
    initial: TriageState = {
        "message_id": message_id,
        "sender": sender,
        "content": content,
        "channel": channel,
        "followup_count": followup_count,
        # Filled by nodes
        "category": "",
        "priority": "",
        "urgency": "",
        "importance": "",
        "sender_type": "",
        "related_ticket_ids": [],
        "related_context": "",
        "group_with": None,
        "action": "",
        "action_reason": "",
        "draft": None,
        "draft_channel": channel,
    }

    return await triage_graph.ainvoke(initial)
