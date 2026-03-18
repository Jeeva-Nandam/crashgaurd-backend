from datetime import datetime, timezone
from typing import List, Optional
from bson import ObjectId
from app.core.database import get_analyses_collection


def _serialize(doc: dict) -> dict:
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


async def save_analysis(user_id: str, label: Optional[str], result: dict) -> dict:
    collection = get_analyses_collection()
    doc = {
        "user_id": user_id,
        "label": label or f"Analysis {datetime.now(timezone.utc).strftime('%d %b %Y %H:%M')}",
        "result": result,
        "created_at": datetime.now(timezone.utc),
    }
    inserted = await collection.insert_one(doc)
    doc["_id"] = inserted.inserted_id
    return _serialize(doc)


async def get_user_analyses(user_id: str, limit: int = 20) -> List[dict]:
    collection = get_analyses_collection()
    cursor = collection.find(
        {"user_id": user_id},
        sort=[("created_at", -1)],
        limit=limit
    )
    docs = await cursor.to_list(length=limit)
    return [_serialize(d) for d in docs]


async def get_analysis_by_id(analysis_id: str, user_id: str) -> Optional[dict]:
    collection = get_analyses_collection()
    doc = await collection.find_one({
        "_id": ObjectId(analysis_id),
        "user_id": user_id  # enforce ownership
    })
    return _serialize(doc) if doc else None


async def delete_analysis(analysis_id: str, user_id: str) -> bool:
    collection = get_analyses_collection()
    result = await collection.delete_one({
        "_id": ObjectId(analysis_id),
        "user_id": user_id
    })
    return result.deleted_count > 0
