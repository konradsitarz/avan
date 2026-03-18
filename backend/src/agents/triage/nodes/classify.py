"""Classify node — determines category, priority, and sender type via LLM structured output."""

import logging
from enum import Enum
from pydantic import BaseModel, Field

from ....core.llm import get_llm
from ..prompts.classify import CLASSIFY_SYSTEM, CLASSIFY_USER
from ..fewshot import load_few_shot_examples

logger = logging.getLogger(__name__)


class Category(str, Enum):
    SAFETY = "safety"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    NOISE = "noise"
    MAINTENANCE = "maintenance"
    BILLING = "billing"
    ACCESS = "access"
    COMPLIANCE = "compliance"
    OTHER = "other"


class ClassifyPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class Urgency(str, Enum):
    """Can it wait? Time-sensitivity axis."""
    IMMEDIATE = "immediate"   # Must act now — active damage, danger, or escalation in progress
    TODAY = "today"           # Needs attention today but not this minute
    THIS_WEEK = "this_week"   # Can wait a few days without consequences
    NO_RUSH = "no_rush"       # Purely informational or low time-pressure


class Importance(str, Enum):
    """How serious? Impact axis."""
    CRITICAL = "critical"     # Safety risk, major property damage, legal exposure
    HIGH = "high"             # Significant resident impact or financial risk
    MODERATE = "moderate"     # Standard issue, limited impact
    LOW = "low"               # Minor inconvenience, cosmetic, informational


class SenderType(str, Enum):
    RESIDENT = "resident"
    VENDOR = "vendor"
    SYSTEM = "system"


class ClassificationResult(BaseModel):
    category: Category = Field(description="Issue category")
    priority: ClassifyPriority = Field(description="Urgency level")
    urgency: Urgency = Field(description="Can it wait? How time-sensitive is this issue.")
    importance: Importance = Field(description="How serious? What is the potential impact if ignored.")
    sender_type: SenderType = Field(description="Who sent the message")


async def classify(state: dict) -> dict:
    llm = get_llm(temperature=0.1).with_structured_output(ClassificationResult)

    # Load few-shot examples from manager overrides
    few_shot = await load_few_shot_examples()

    prompt = CLASSIFY_USER.format(
        sender=state["sender"],
        channel=state["channel"],
        followup_count=state["followup_count"],
        content=state["content"],
    )

    # Inject few-shot examples between system prompt and user prompt
    full_prompt = CLASSIFY_SYSTEM
    if few_shot:
        full_prompt += f"\n\n{few_shot}"
    full_prompt += f"\n\n{prompt}"

    try:
        result = llm.invoke(full_prompt)
    except Exception as e:
        logger.warning(f"Structured classify failed, using defaults: {e}")
        result = ClassificationResult(
            category=Category.OTHER,
            priority=ClassifyPriority.MEDIUM,
            urgency=Urgency.THIS_WEEK,
            importance=Importance.MODERATE,
            sender_type=SenderType.RESIDENT,
        )

    # Auto-escalation override: 3+ follow-ups always urgent priority
    # but urgency stays as LLM decided — a broken gate with 3 followups
    # is urgent priority but not "immediate" like active flooding
    priority = result.priority.value
    if state["followup_count"] >= 3:
        priority = "urgent"

    return {
        "category": result.category.value,
        "priority": priority,
        "urgency": result.urgency.value,
        "importance": result.importance.value,
        "sender_type": result.sender_type.value,
    }
