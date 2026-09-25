"""
Space management API routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, status
from brain.src.api.deps import get_current_user_id
from brain.src.schemas.spaces import SpaceCreate, SpaceUpdate
from brain.src import services

router = APIRouter(prefix="/spaces", tags=["Spaces"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_space(
    payload: SpaceCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new Space."""
    return services.spaces_service.create_space(payload, current_user_id)


@router.get("", status_code=status.HTTP_200_OK)
def list_spaces(
    status: Optional[str] = None,
    current_user_id: str = Depends(get_current_user_id)
):
    """List all Spaces owned by the user."""
    return services.spaces_service.list_spaces(current_user_id, status=status)


@router.get("/{space_id}", status_code=status.HTTP_200_OK)
def get_space(space_id: str):
    """Get a Space by ID."""
    return services.spaces_service.get_space(space_id)


@router.patch("/{space_id}", status_code=status.HTTP_200_OK)
def update_space(
    space_id: str,
    payload: SpaceUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update fields of an existing Space."""
    return services.spaces_service.update_space(space_id, payload, current_user_id)


@router.delete("/{space_id}", status_code=status.HTTP_200_OK)
def delete_space(
    space_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete a Space by ID."""
    return services.spaces_service.delete_space(space_id, current_user_id)
