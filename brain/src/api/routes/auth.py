"""
Authentication API routes for DreamWeave.
Handles registration, login, token refresh, logout, and current user profile.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, status, Header
from pydantic import BaseModel, Field

from brain.src.api.deps import get_authenticated_user_id, get_token_from_header
from brain.src.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    UserOut
)
from brain.src.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


class RegisterResponse(BaseModel):
    tokens: TokenResponse
    user: UserOut


class LoginResponse(BaseModel):
    tokens: TokenResponse
    user: UserOut


class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = Field(default=None, description="Optional refresh token to revoke alongside access token")


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister):
    """
    Register a new user account.
    Returns access and refresh tokens along with user profile.
    """
    token_resp, user_data = auth_service.register_user(payload)
    return {
        "tokens": token_resp,
        "user": user_data
    }


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(payload: UserLogin):
    """
    Authenticate user credentials.
    Returns access and refresh tokens along with user profile.
    """
    token_resp, user_data = auth_service.login_user(payload)
    return {
        "tokens": token_resp,
        "user": user_data
    }


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
def refresh(payload: RefreshTokenRequest):
    """
    Rotate refresh token.
    Invalidates submitted refresh token and returns a new token pair.
    """
    return auth_service.refresh_tokens(payload.refresh_token)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    payload: Optional[LogoutRequest] = None,
    authorization: Optional[str] = Header(None)
):
    """
    Log out user.
    Revokes the provided Bearer access token and optional refresh token.
    """
    token = get_token_from_header(authorization)
    refresh_token = payload.refresh_token if payload else None
    return auth_service.logout_user(token_str=token, refresh_token_str=refresh_token)


@router.get("/me", response_model=UserOut, status_code=status.HTTP_200_OK)
def get_me(current_user_id: str = Depends(get_authenticated_user_id)):
    """
    Get current authenticated user profile.
    Requires a valid, non-revoked Bearer access token.
    """
    return auth_service.get_current_user_profile(current_user_id)
