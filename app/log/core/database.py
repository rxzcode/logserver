from motor.motor_asyncio import AsyncIOMotorClient
from core.config import MONGODB_URI
from pymongo import ASCENDING

client = AsyncIOMotorClient(MONGODB_URI)
db = client["logdb"]
logs = db["logs"]
tenants = db["tenants"]

async def ensure_indexes():
    await logs.create_index([("tenant_id", ASCENDING), ("severity", ASCENDING)], name="tenant_severity_idx")