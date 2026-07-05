from datetime import datetime
from typing import Optional
from bson import ObjectId


class UserModel:
    collection = "users"

    @staticmethod
    def document(
        name: str,
        email: str,
        hashed_password: str,
        role: str,
        created_by: Optional[str] = None,
    ) -> dict:
        return {
            "name": name,
            "email": email,
            "password": hashed_password,
            "role": role,
            "created_by": created_by,
            "is_active": True,
            "created_at": datetime.utcnow(),
        }