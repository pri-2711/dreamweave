"""
Pydantic schemas for Conversations and Messages APIs.
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Conversation title")


class MessageCreate(BaseModel):
    role: str = Field(default="user", description="Message role: user, assistant, system")
    content: str = Field(..., min_length=1, description="Message text content")
    content_ids: Optional[List[str]] = Field(default=None, description="Context content ObjectIds")
    knowledge_ids: Optional[List[str]] = Field(default=None, description="Context knowledge ObjectIds")
    generated_content_ids: Optional[List[str]] = Field(default=None, description="Generated content ObjectIds")
