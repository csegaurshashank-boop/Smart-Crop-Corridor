from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from app.core.config import settings
from typing import Optional

client: Optional[AsyncIOMotorClient] = None
database: Optional[AsyncIOMotorDatabase] = None


async def connect_db():
    global client, database
    client = AsyncIOMotorClient(settings.MONGO_URI)
    database = client[settings.DATABASE_NAME]
    print(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")


async def close_db():
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    if database is None:
        raise RuntimeError("Database not connected. Call connect_db() first.")
    return database