from beanie import Document
from pydantic import Field
from datetime import datetime, timezone
from enum import Enum

class ConditionOperator(str, Enum):
    GTE = "gte"
    LTE = "lte"
    EQ = "eq"
    CONTAINS = "contains"

class RuleAction(str, Enum):
    SET_PRIORITY = "set_priority"
    ASSIGN_TO = "assign_to"
    NOTIFY_ADMIN = "notify_admin"
    AUTO_RESPOND = "auto_respond"

class Rule(Document):
    name: str
    description: str
    condition_field: str
    condition_operator: ConditionOperator
    condition_value: str
    action: RuleAction
    action_value: str
    enabled: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "rules"
