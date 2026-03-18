from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings

client: AsyncIOMotorClient = None


async def connect_db():
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URL)
    # Ping to verify connection
    await client.admin.command("ping")
    print(f"✅ Connected to MongoDB Atlas — database: {settings.DATABASE_NAME}")

    print("DB URL:", settings.MONGODB_URL)
    print("DB NAME:", settings.DATABASE_NAME)
async def close_db():
    global client
    if client:
        client.close()
        print("🔌 MongoDB connection closed")


def get_database():
    return client[settings.DATABASE_NAME]


# ── Collection helpers ──────────────────────────────────────────────────────
def get_users_collection():
    return get_database()["users"]


def get_otp_collection():
    return get_database()["otp_tokens"]


def get_analyses_collection():
    return get_database()["analyses"]


def get_refresh_tokens_collection():
    return get_database()["refresh_tokens"]
