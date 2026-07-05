from bson import ObjectId  # type: ignore[import-untyped]
from datetime import datetime
from app.database import get_db  # type: ignore
from app.core.security import hash_password, verify_password, create_access_token  # type: ignore
from app.models.user import UserModel  # type: ignore
from fastapi import HTTPException, status  # type: ignore
from typing import List, Optional


async def register_user(name: str, email: str, password: str, role: str, created_by: Optional[str] = None) -> dict:
    db = get_db()
    existing = await db[UserModel.collection].find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    doc = UserModel.document(name, email, hash_password(password), role, created_by)
    result = await db[UserModel.collection].insert_one(doc)
    doc["_id"] = result.inserted_id
    return _serialize(doc)


async def authenticate_user(email: str, password: str) -> dict:
    db = get_db()
    user = await db[UserModel.collection].find_one({"email": email})
    if not user or not verify_password(password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"sub": str(user["_id"]), "role": user["role"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user["role"],
        "user_id": str(user["_id"]),
    }


async def list_users(role: Optional[str] = None) -> List[dict]:
    db = get_db()
    query = {"role": role} if role else {}
    users = await db[UserModel.collection].find(query).to_list(length=100)
    return [_serialize(u) for u in users]


async def get_user_by_id(user_id: str) -> Optional[dict]:
    db = get_db()
    user = await db[UserModel.collection].find_one({"_id": ObjectId(user_id)})
    return _serialize(user) if user else None


def _serialize(user: dict) -> dict:
    user["id"] = str(user.pop("_id"))
    user.pop("password", None)
    if "created_at" in user and hasattr(user["created_at"], "isoformat"):
        user["created_at"] = user["created_at"].isoformat()
    return user