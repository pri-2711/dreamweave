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
def get_space(
    space_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Get a Space by ID (requires viewer permission)."""
    return services.spaces_service.get_space(space_id, current_user_id=current_user_id)


@router.patch("/{space_id}", status_code=status.HTTP_200_OK)
def update_space(
    space_id: str,
    payload: SpaceUpdate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Update fields of an existing Space (requires editor/owner)."""
    return services.spaces_service.update_space(space_id, payload, current_user_id)


@router.delete("/{space_id}", status_code=status.HTTP_200_OK)
def delete_space(
    space_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete a Space by ID (strictly requires owner)."""
    return services.spaces_service.delete_space(space_id, current_user_id)


# --- Space Collaborator / Member Endpoints ---

@router.post("/{space_id}/members", status_code=status.HTTP_201_CREATED)
def add_space_member(
    space_id: str,
    payload: dict,
    current_user_id: str = Depends(get_current_user_id)
):
    """Add or update a collaborator in a space (owner only)."""
    user_id = payload.get("user_id")
    role = payload.get("role", "viewer")
    return services.spaces_service.add_space_member(
        space_id=space_id,
        member_user_id=user_id,
        role=role,
        current_user_id=current_user_id
    )


@router.get("/{space_id}/members", status_code=status.HTTP_200_OK)
def list_space_members(
    space_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """List collaborators in a space (members only)."""
    return services.spaces_service.list_space_members(space_id, current_user_id=current_user_id)


@router.delete("/{space_id}/members/{user_id}", status_code=status.HTTP_200_OK)
def remove_space_member(
    space_id: str,
    user_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Remove a collaborator from a space (owner only)."""
    return services.spaces_service.remove_space_member(
        space_id=space_id,
        target_user_id=user_id,
        current_user_id=current_user_id
    )

