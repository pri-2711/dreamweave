"""
AI Content persistence API routes.
"""

from typing import Optional
from fastapi import APIRouter, Depends, status
from brain.src.api.deps import get_current_user_id
from brain.src.schemas.ai_content import AIContentCreate, AIContentUpdate
from brain.src import services

router = APIRouter(prefix="/ai-content", tags=["AI Content"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_ai_content(
    payload: AIContentCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create persistent AI Content."""
    return services.ai_content_service.create_ai_content(payload, current_user_id)


@router.get("", status_code=status.HTTP_200_OK)
def list_ai_content(
    space_id: str,
    type: Optional[str] = None
):
    """List persistent AI content items in a space."""
    return services.ai_content_service.list_ai_content(space_id=space_id, content_type=type)


@router.get("/{id}", status_code=status.HTTP_200_OK)
def get_ai_content(id: str):
    """Get persistent AI content item by ID."""
    return services.ai_content_service.get_ai_content(id)


@router.patch("/{id}", status_code=status.HTTP_200_OK)
def update_ai_content(
    id: str,
    payload: AIContentUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update fields of an AI content item."""
    return services.ai_content_service.update_ai_content(id, payload, current_user_id)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
def delete_ai_content(
    id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete an AI content item by ID."""
    return services.ai_content_service.delete_ai_content(id, current_user_id)
