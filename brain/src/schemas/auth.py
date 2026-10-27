"""
Pydantic schemas for Authentication and User management.
"""

import re
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class UserRegister(BaseModel):
    """Payload for user registration."""
    email: str = Field(..., min_length=3, max_length=254, description="User's email address")
    name: str = Field(..., min_length=1, max_length=100, description="Full name or display name")
    password: str = Field(..., min_length=8, max_length=72, description="Password (8-72 characters)")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            clean = v.strip().lower()
            if not clean or not EMAIL_REGEX.match(clean):
                raise ValueError("Invalid email address format.")
            return clean
        raise ValueError("Email must be a string.")

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        if isinstance(v, str):
            clean = v.strip()
            if not clean:
                raise ValueError("Name cannot be empty or only whitespace.")
            return clean
        return v

    @field_validator("password")
    @classmethod
    def validate_password_bytes(cls, v: str) -> str:
        # Enforce maximum 72 bytes due to bcrypt limitation
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 bytes.")
        return v


class UserLogin(BaseModel):
    """Payload for user login."""
    email: str = Field(..., min_length=3, max_length=254, description="User's email address")
    password: str = Field(..., min_length=1, max_length=72, description="Password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        if isinstance(v, str):
            clean = v.strip().lower()
            if not clean or not EMAIL_REGEX.match(clean):
                raise ValueError("Invalid email address format.")
            return clean
        raise ValueError("Email must be a string.")



class TokenResponse(BaseModel):
    """Token response containing access and refresh tokens."""
    access_token: str = Field(..., description="JWT Bearer access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration window in seconds")


class RefreshTokenRequest(BaseModel):
    """Payload for token refresh."""
    refresh_token: str = Field(..., min_length=1, description="Valid refresh token")


class UserProfile(BaseModel):
    """User public profile details."""
    name: str
    avatar_url: Optional[str] = None
    bio: Optional[str] = None


class UserPreferences(BaseModel):
    """User preferences."""
    theme: str = "light"
    language: str = "en"


class UserOut(BaseModel):
    """
    Public representation of a User.
    Strictly excludes password_hash and internal auth structures.
    """
    id: str = Field(..., description="User unique 24-hex string identifier")
    email: str = Field(..., description="Normalized email address")
    profile: UserProfile
    preferences: UserPreferences
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class SpaceMemberAdd(BaseModel):
    """Payload for adding or updating a collaborator in a space."""
    user_id: str = Field(..., min_length=24, max_length=24, description="Collaborator 24-character ObjectId string")
    role: str = Field(default="viewer", description="Collaborator role: 'editor' or 'viewer'")

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        clean = v.strip().lower()
        if clean not in ("editor", "viewer"):
            raise ValueError("Role must be either 'editor' or 'viewer'.")
        return clean


class SpaceMemberOut(BaseModel):
    """Representation of a space member record."""
    id: Optional[str] = None
    space_id: str
    user_id: str
    role: str
    joined_at: Optional[datetime] = None
