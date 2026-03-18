from fastapi import APIRouter, HTTPException, Depends
from datetime import timezone
from bson import ObjectId
from app.core.database import get_database
from app.core.dependencies import get_verified_user

router = APIRouter(prefix="/admin", tags=["Admin"])


def _ser(doc: dict) -> dict:
    if doc:
        doc["id"] = str(doc.pop("_id"))
    return doc


#@router.get("/users")
# async def list_all_users(current_user: dict = Depends(get_verified_user)):
#     if current_user.get("role") != "Founder":
#         raise HTTPException(status_code=403, detail="Admin access restricted to Founders.")

#     db = get_database()
#     users_col = db["users"]
#     analyses_col = db["analyses"]

#     users = await users_col.find(
#         {}, {"password_hash": 0}
#     ).sort("created_at", -1).to_list(500)

#     for u in users:
#         _ser(u)

#     total_analyses = await analyses_col.count_documents({})
#     high_risk = await analyses_col.count_documents({"result.risk_level": "HIGH RISK"})

#     return {
#         "users": users,
#         "stats": {
#             "total_users": len(users),
#             "verified_users": sum(1 for u in users if u.get("is_email_verified")),
#             "total_analyses": total_analyses,
#             "high_risk_count": high_risk,
#         },
#     }
@router.get("/users")
async def list_all_users():
    db = get_database()
    users_col = db["users"]
    analyses_col = db["analyses"]

    users = await users_col.find(
        {}, {"password_hash": 0}
    ).sort("created_at", -1).to_list(500)

    for u in users:
        _ser(u)

    total_analyses = await analyses_col.count_documents({})
    high_risk = await analyses_col.count_documents({"result.risk_level": "HIGH RISK"})

    return {
        "users": users,
        "stats": {
            "total_users": len(users),
            "verified_users": sum(1 for u in users if u.get("is_email_verified")),
            "total_analyses": total_analyses,
            "high_risk_count": high_risk,
        },
    }


# @router.get("/users/{user_id}/analyses")
# async def get_user_analyses_admin(
#     user_id: str,
#     current_user: dict = Depends(get_verified_user),
# ):
#     if current_user.get("role") != "Founder":
#         raise HTTPException(status_code=403, detail="Admin access restricted to Founders.")

#     db = get_database()
#     col = db["analyses"]
#     docs = await col.find(
#         {"user_id": user_id}
#     ).sort("created_at", -1).to_list(50)

#     for d in docs:
#         _ser(d)

#     return {"analyses": docs}
@router.get("/users/{user_id}/analyses")
async def get_user_analyses_admin(user_id: str):
    db = get_database()
    col = db["analyses"]

    docs = await col.find(
        {"user_id": user_id}
    ).sort("created_at", -1).to_list(50)

    for d in docs:
        _ser(d)

    return {"analyses": docs}