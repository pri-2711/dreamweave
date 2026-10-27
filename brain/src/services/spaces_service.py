"""
Business logic service for Spaces.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from brain.src.database.repositories import spaces as spaces_repo
from brain.src.database.repositories import activity as activity_repo
from brain.src.schemas.spaces import SpaceCreate, SpaceUpdate
from brain.src.utils.serialization import parse_object_id, serialize_doc, serialize_docs


def create_space(data: SpaceCreate, current_user_id: str) -> Dict[str, Any]:
    """Create a new Space and log activity."""
    owner_oid = parse_object_id(current_user_id, param_name="user_id")

    doc = spaces_repo.create_space(
        owner_id=owner_oid,
        name=data.name.strip(),
        description=data.description or "",
        icon=data.icon,
        cover_image_url=data.cover_image_url,
        cover_position=data.cover_position,
        status=data.status or "active",
        visibility=data.visibility or "private",
        is_favourite=data.is_favourite,
        is_archived=data.is_archived
    )

    space_id = doc["_id"]
    activity_repo.log_activity(
        space_id=space_id,
        user_id=owner_oid,
        action="space_created",
        target_type="space",
        target_id=space_id
    )

    return serialize_doc(doc)


def get_space(space_id: str, current_user_id: Optional[str] = None) -> Dict[str, Any]:
    """Get a Space by ID (requires viewer role if user_id provided)."""
    if current_user_id:
        from brain.src.services.authorization import check_space_access
        check_space_access(space_id, current_user_id, required_role="viewer")

    sid = parse_object_id(space_id, param_name="space_id")
    space = spaces_repo.get_space_by_id(sid)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{space_id}' not found."
        )
    return serialize_doc(space)


def list_spaces(current_user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all Spaces where current user is owner or collaborator without duplicates."""
    owner_oid = parse_object_id(current_user_id, param_name="user_id")
    spaces = spaces_repo.list_spaces_for_user(user_id=owner_oid, status=status)
    return serialize_docs(spaces)


def update_space(space_id: str, data: SpaceUpdate, current_user_id: str) -> Dict[str, Any]:
    """Update fields of an existing Space (requires editor or owner role)."""
    from brain.src.services.authorization import check_space_access
    check_space_access(space_id, current_user_id, required_role="editor")

    sid = parse_object_id(space_id, param_name="space_id")
    existing = spaces_repo.get_space_by_id(sid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{space_id}' not found."
        )

    updates = {}
    if data.name is not None:
        updates["name"] = data.name.strip()
    if data.description is not None:
        updates["description"] = data.description
    if data.icon is not None:
        updates["icon"] = data.icon
    if data.cover_image_url is not None:
        updates["cover.image_url"] = data.cover_image_url
    if data.cover_position is not None:
        updates["cover.position"] = data.cover_position
    if data.status is not None:
        updates["status"] = data.status
    if data.visibility is not None:
        updates["settings.visibility"] = data.visibility
    if data.is_favourite is not None:
        updates["organization.is_favourite"] = data.is_favourite
    if data.is_archived is not None:
        updates["organization.is_archived"] = data.is_archived

    if updates:
        spaces_repo.update_space(sid, updates)
        user_oid = parse_object_id(current_user_id, param_name="user_id")
        activity_repo.log_activity(
            space_id=sid,
            user_id=user_oid,
            action="space_updated",
            target_type="space",
            target_id=sid
        )

    updated_space = spaces_repo.get_space_by_id(sid)
    return serialize_doc(updated_space)


def delete_space(space_id: str, current_user_id: str) -> Dict[str, Any]:
    """Delete a Space by ID (strictly requires owner role)."""
    from brain.src.services.authorization import check_space_access
    check_space_access(space_id, current_user_id, required_role="owner")

    sid = parse_object_id(space_id, param_name="space_id")
    existing = spaces_repo.get_space_by_id(sid)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{space_id}' not found."
        )

    spaces_repo.delete_space(sid)
    return {"message": f"Space '{space_id}' successfully deleted."}


def add_space_member(space_id: str, member_user_id: str, role: str, current_user_id: str) -> Dict[str, Any]:
    """Add or update a collaborator in a space (strictly requires owner role)."""
    from brain.src.services.authorization import check_space_access
    check_space_access(space_id, current_user_id, required_role="owner")

    sid = parse_object_id(space_id, param_name="space_id")
    uid = parse_object_id(member_user_id, param_name="member_user_id")

    record = spaces_repo.add_space_member(space_id=sid, user_id=uid, role=role)
    return serialize_doc(record)


def list_space_members(space_id: str, current_user_id: str) -> List[Dict[str, Any]]:
    """List all members of a space (requires viewer role)."""
    from brain.src.services.authorization import check_space_access
    check_space_access(space_id, current_user_id, required_role="viewer")

    sid = parse_object_id(space_id, param_name="space_id")
    members = spaces_repo.list_space_members(sid)
    return serialize_docs(members)


def remove_space_member(space_id: str, target_user_id: str, current_user_id: str) -> Dict[str, Any]:
    """Remove a collaborator from a space (strictly requires owner role)."""
    from brain.src.services.authorization import check_space_access
    check_space_access(space_id, current_user_id, required_role="owner")

    sid = parse_object_id(space_id, param_name="space_id")
    t_uid = parse_object_id(target_user_id, param_name="target_user_id")

    success = spaces_repo.remove_space_member(space_id=sid, user_id=t_uid)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove space member (member not found or member is the space owner)."
        )

    return {"message": f"Member '{target_user_id}' removed from space '{space_id}'."}

