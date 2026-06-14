from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.services.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Auth"])


class AuthRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    user_id: str
    has_company_profile: bool


class RegisterResponse(BaseModel):
    access_token: str
    user_id: str


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(body: AuthRequest):
    async with get_db() as session:
        existing = await session.execute(select(User).where(User.email == body.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(email=body.email, hashed_password=hash_password(body.password))
        session.add(user)
        await session.flush()
        token = create_access_token(user.id)
        logger.info("Registered new user: %s", user.email)
        return RegisterResponse(access_token=token, user_id=user.id)


@router.post("/login", response_model=LoginResponse)
async def login(body: AuthRequest):
    async with get_db() as session:
        result = await session.execute(select(User).where(User.email == body.email))
        user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id)
    logger.info("User logged in: %s", user.email)
    return LoginResponse(
        access_token=token,
        user_id=user.id,
        has_company_profile=user.has_company_profile,
    )
