"""
Content Items API routes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status
from brain.src.api.deps import get_current_user_id
from brain.src.schemas.content import ContentCreate, ContentUpdate
from brain.src import services
from brain.src.services.ingestion_service import ingest_content_item

router = APIRouter(prefix="/content", tags=["Content"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_content(
    payload: ContentCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new Content Item."""
    return services.content_service.create_content_item(payload, current_user_id)


@router.get("", status_code=status.HTTP_200_OK)
def list_content(
    space_id: Optional[str] = None,
    type: Optional[str] = None,
    is_favourite: Optional[bool] = None,
    is_archived: Optional[bool] = None
):
    """List content items with optional filters."""
    return services.content_service.list_content_items(
        space_id=space_id,
        item_type=type,
        is_favourite=is_favourite,
        is_archived=is_archived
    )


@router.get("/{content_id}", status_code=status.HTTP_200_OK)
def get_content(content_id: str):
    """Get a content item by ID."""
    return services.content_service.get_content_item(content_id)


@router.patch("/{content_id}", status_code=status.HTTP_200_OK)
def update_content(
    content_id: str,
    payload: ContentUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update fields of a content item."""
    return services.content_service.update_content_item(content_id, payload, current_user_id)


@router.delete("/{content_id}", status_code=status.HTTP_200_OK)
def delete_content(
    content_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete a content item by ID."""
    return services.content_service.delete_content_item(content_id, current_user_id)


@router.post("/{content_id}/ingest", status_code=status.HTTP_200_OK)
def ingest_content(
    content_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Trigger Knowledge Ingestion Pipeline for a content item:
    Content -> Extraction -> Clean -> Knowledge -> Chunks -> Embeddings -> MongoDB.
    """
    return ingest_content_item(content_id, current_user_id)
