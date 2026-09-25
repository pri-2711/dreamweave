"""
Pydantic schemas for Vision Boards and Vision Board Items APIs.
"""

from typing import Optional
from pydantic import BaseModel, Field


class VisionBoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Vision board name")
    width: int = Field(default=1920, description="Canvas width")
    height: int = Field(default=1080, description="Canvas height")


class VisionBoardUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    width: Optional[int] = None
    height: Optional[int] = None


class VisionBoardItemCreate(BaseModel):
    content_id: Optional[str] = Field(default=None, description="Linked content item ObjectId")
    ai_content_id: Optional[str] = Field(default=None, description="Linked AI content ObjectId")
    x: float = Field(default=0.0, description="Canvas x position")
    y: float = Field(default=0.0, description="Canvas y position")
    width: float = Field(default=300.0, description="Item width")
    height: float = Field(default=200.0, description="Item height")
    rotation: float = Field(default=0.0, description="Rotation degrees")
    z_index: int = Field(default=0, description="Layer order")
    border_radius: Optional[float] = Field(default=None, description="Corner border radius")


class VisionBoardItemUpdate(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    rotation: Optional[float] = None
    z_index: Optional[int] = None
    border_radius: Optional[float] = None
