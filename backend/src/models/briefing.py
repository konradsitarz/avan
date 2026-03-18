from beanie import Document
from pydantic import Field
from datetime import datetime, timezone


class Briefing(Document):
    """Cached briefing — regenerated only when messages change."""
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str
    issues: list[dict] = []
    stats: dict = {}
    stale: bool = False

    class Settings:
        name = "briefings"
