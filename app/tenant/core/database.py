from motor.motor_asyncio import AsyncIOMotorClient
from core.config import MONGODB_URI

client = AsyncIOMotorClient(MONGODB_URI)
db = client["logdb"]
logs = db["logs"]
tenants = db["tenants"]