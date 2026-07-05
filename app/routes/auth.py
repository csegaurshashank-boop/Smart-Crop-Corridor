from fastapi import APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Depends
from app.schemas.user import UserCreate, TokenResponse, UserResponse
from app.services.user_service import register_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=dict, summary="Register a new user")
async def register(user: UserCreate):
    return await register_user(user.name, user.email, user.password, user.role)


@router.post("/login", response_model=TokenResponse, summary="Login and get JWT token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    return await authenticate_user(form_data.username, form_data.password)