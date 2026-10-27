"""
Authorization and Space Permission Service for DreamWeave.
Enforces role-based access control (owner, editor, viewer) across spaces and sub-resources.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from bson import ObjectId

from brain.src.database.repositories import spaces as spaces_repo
from brain.src.utils.serialization import parse_object_id

# Role hierarchy: owner > editor > viewer
ROLE_HIERARCHY = {
    "viewer": 1,
    "editor": 2,
    "owner": 3
}


def get_user_space_role(space_id: Any, user_id: Any) -> Optional[str]:
    """
    Determine the role of user_id in space_id.
    Returns 'owner', 'editor', 'viewer', or None if not a member.
    """
    sid = space_id if isinstance(space_id, ObjectId) else parse_object_id(str(space_id), param_name="space_id")
    uid = user_id if isinstance(user_id, ObjectId) else parse_object_id(str(user_id), param_name="user_id")

    space = spaces_repo.get_space_by_id(sid)
    if not space:
        return None

    # Check if space owner
    if space.get("owner_id") == uid:
        return "owner"

    # Check space_members record
    member = spaces_repo.get_space_member(sid, uid)
    if member:
        return member.get("role", "viewer")

    return None


def check_space_access(
    space_id: Any,
    user_id: Any,
    required_role: str = "viewer"
) -> Dict[str, Any]:
    """
    Verify that user_id has at least `required_role` in space_id.
    Raises:
      - 404 NOT FOUND if space does not exist.
      - 403 FORBIDDEN if user is not a member or role level is insufficient.
    Returns the space document if allowed.
    """
    sid = space_id if isinstance(space_id, ObjectId) else parse_object_id(str(space_id), param_name="space_id")
    space = spaces_repo.get_space_by_id(sid)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{space_id}' not found."
        )

    user_role = get_user_space_role(sid, user_id)
    if not user_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You are not a member of this space."
        )

    required_level = ROLE_HIERARCHY.get(required_role, 1)
    user_level = ROLE_HIERARCHY.get(user_role, 0)

    if user_level < required_level:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: Requires '{required_role}' permission (your role: '{user_role}')."
        )

    return space
