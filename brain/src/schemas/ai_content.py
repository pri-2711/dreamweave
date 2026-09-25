"""
Pydantic schemas for AI Content APIs.
"""

from typing import Optional, List, Union, Dict, Any
from pydantic import BaseModel, Field


class AIContentCreate(BaseModel):
    space_id: str = Field(..., description="Target Space ObjectId")
    type: str = Field(..., description="AI Content type (suggestion, itinerary, summary, checklist, etc.)")
    content: Union[str, Dict[str, Any], List[Any]] = Field(..., description="Generated AI content payload")
    title: Optional[str] = Field(default=None, description="Title of AI content")
    source_content_ids: Optional[List[str]] = Field(default=None, description="Source content ObjectIds")
    source_knowledge_ids: Optional[List[str]] = Field(default=None, description="Source knowledge ObjectIds")
    asset_id: Optional[str] = Field(default=None, description="Associated asset ObjectId")
    is_favourite: bool = Field(default=False)
    is_archived: bool = Field(default=False)


class AIContentUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[Union[str, Dict[str, Any], List[Any]]] = None
    is_favourite: Optional[bool] = None
    is_archived: Optional[bool] = None
