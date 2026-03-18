from datetime import datetime, timezone
from typing import Optional
from bson import ObjectId
from app.core.database import get_users_collection, get_refresh_tokens_collection
from app.core.security import hash_password, verify_password
from app.models.schemas import RegisterRequest, BusinessProfileRequest


def _serialize_user(user: dict) -> dict:
    """Convert MongoDB document to JSON-safe dict."""
    if user:
        user["id"] = str(user.pop("_id"))
    return user


# ── Create ───────────────────────────────────────────────────────────────────
async def create_user(data: RegisterRequest) -> dict:
    collection = get_users_collection()
    now = datetime.now(timezone.utc)

    user_doc = {
        "full_name": data.full_name,
        "email": data.email.lower(),
        "password_hash": hash_password(data.password),
        "phone_number": data.phone_number,
        "role": data.role,
        "is_email_verified": True,
        "onboarding_complete": False,
        "business_profile": None,
        "integrations": {
            "stripe": None,
            "quickbooks": None,
            "google_sheets": None,
        },
        "created_at": now,
        "updated_at": now,
    }

    result = await collection.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    return _serialize_user(user_doc)


# ── Read ─────────────────────────────────────────────────────────────────────
async def get_user_by_email(email: str) -> Optional[dict]:
    collection = get_users_collection()
    user = await collection.find_one({"email": email.lower()})
    return _serialize_user(user) if user else None


async def get_user_by_id(user_id: str) -> Optional[dict]:
    collection = get_users_collection()
    user = await collection.find_one({"_id": ObjectId(user_id)})
    return _serialize_user(user) if user else None


async def email_exists(email: str) -> bool:
    collection = get_users_collection()
    return await collection.find_one({"email": email.lower()}) is not None


# ── Update ───────────────────────────────────────────────────────────────────
async def mark_email_verified(email: str):
    collection = get_users_collection()
    await collection.update_one(
        {"email": email.lower()},
        {"$set": {"is_email_verified": True, "updated_at": datetime.now(timezone.utc)}}
    )


async def update_business_profile(user_id: str, data: BusinessProfileRequest) -> dict:
    collection = get_users_collection()
    profile = data.model_dump(exclude_none=True)

    result = await collection.find_one_and_update(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "business_profile": profile,
                "onboarding_complete": True,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        return_document=True,
    )
    return _serialize_user(result)


async def update_password(user_id: str, new_password: str):
    collection = get_users_collection()
    await collection.update_one(
        {"_id": ObjectId(user_id)},
        {
            "$set": {
                "password_hash": hash_password(new_password),
                "updated_at": datetime.now(timezone.utc),
            }
        }
    )


# ── Authentication ───────────────────────────────────────────────────────────
async def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return user


# ── Refresh Tokens ───────────────────────────────────────────────────────────
async def store_refresh_token(user_id: str, token: str):
    collection = get_refresh_tokens_collection()
    await collection.insert_one({
        "user_id": user_id,
        "token": token,
        "created_at": datetime.now(timezone.utc),
    })


async def validate_and_rotate_refresh_token(token: str) -> Optional[str]:
    """Returns user_id if valid, deletes the used token (rotation)."""
    collection = get_refresh_tokens_collection()
    record = await collection.find_one_and_delete({"token": token})
    if not record:
        return None
    return record["user_id"]


async def revoke_all_refresh_tokens(user_id: str):
    """Logout from all devices."""
    collection = get_refresh_tokens_collection()
    await collection.delete_many({"user_id": user_id})
