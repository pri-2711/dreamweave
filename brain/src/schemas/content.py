"""
Pydantic schemas for Content Items APIs.
"""

from typing import Optional, List
from pydantic import BaseModel, Field

VALID_CONTENT_TYPES = {
    "image", "pdf", "note", "link", "video", "social_post",
    "sticker", "screenshot", "ticket", "document", "map", "text", "other"
}


class SourceSchema(BaseModel):
    kind: str = Field(default="upload", description="Source kind: upload, external, created")
    url: Optional[str] = Field(default=None, description="Source URL")
    platform: Optional[str] = Field(default=None, description="Source platform name")


class ContentCreate(BaseModel):
    space_id: str = Field(..., description="Target Space ObjectId")
    type: str = Field(..., description="Content type (image, pdf, note, link, ticket, etc.)")
    title: Optional[str] = Field(default=None, description="Content title")
    description: Optional[str] = Field(default=None, description="Content description")
    source: Optional[SourceSchema] = Field(default=None, description="Source info")
    asset_id: Optional[str] = Field(default=None, description="Associated asset ObjectId")
    tags: Optional[List[str]] = Field(default=None, description="List of tag strings")
    is_favourite: bool = Field(default=False, description="Favourite flag")
    is_archived: bool = Field(default=False, description="Archived flag")


class ContentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    source: Optional[SourceSchema] = None
    asset_id: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favourite: Optional[bool] = None
    is_archived: Optional[bool] = None
