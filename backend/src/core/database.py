from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
import os

from ..models.message import Message
from ..models.rule import Rule
from ..models.briefing import Briefing
from ..models.override import TriageOverride

async def init_db():
    """Initialize database connection and beanie ODM"""
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://mongodb:27017")
    database_name = os.getenv("DATABASE_NAME", "nava")

    client = AsyncIOMotorClient(mongodb_url)
    database = client[database_name]

    await init_beanie(
        database=database,
        document_models=[Message, Rule, Briefing, TriageOverride]
    )
