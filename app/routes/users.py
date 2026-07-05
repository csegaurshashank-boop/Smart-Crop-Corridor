from fastapi import APIRouter, Depends, HTTPException
from app.schemas.user import UserCreate
from app.services.user_service import register_user, list_users, get_user_by_id
from app.core.dependencies import require_role, get_current_user
from typing import Optional

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("/create-manager", summary="Admin creates a manager account")
async def create_manager(
    user: UserCreate,
    current_user: dict = Depends(require_role("admin", "super_admin")),
):
    return await register_user(
        name=user.name,
        email=user.email,
        password=user.password,
        role="manager",
        created_by=current_user["user_id"],
    )


@router.get("/list", summary="List users by role")
async def get_users(
    role: Optional[str] = None,
    current_user: dict = Depends(require_role("admin", "super_admin", "manager")),
):
    return await list_users(role)


@router.get("/me", summary="Get current logged-in user")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await get_user_by_id(current_user["user_id"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user