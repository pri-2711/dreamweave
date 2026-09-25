"""
Pydantic schemas for Spaces APIs.
"""

from typing import Optional
from pydantic import BaseModel, Field


class SpaceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Space name")
    description: Optional[str] = Field(default="", description="Space description")
    icon: Optional[str] = Field(default=None, description="Icon emoji or identifier")
    cover_image_url: Optional[str] = Field(default=None, description="Cover image URL")
    cover_position: Optional[str] = Field(default=None, description="Cover position settings")
    status: Optional[str] = Field(default="active", description="Space status")
    visibility: Optional[str] = Field(default="private", description="Visibility setting")
    is_favourite: bool = Field(default=False, description="Favourite flag")
    is_archived: bool = Field(default=False, description="Archived flag")


class SpaceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    icon: Optional[str] = None
    cover_image_url: Optional[str] = None
    cover_position: Optional[str] = None
    status: Optional[str] = None
    visibility: Optional[str] = None
    is_favourite: Optional[bool] = None
    is_archived: Optional[bool] = None
