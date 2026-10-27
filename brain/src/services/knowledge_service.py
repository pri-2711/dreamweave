"""
Business logic service for Knowledge entries extracted from Content Items.
"""

from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from brain.src.database.repositories import knowledge as knowledge_repo
from brain.src.database.repositories import content as content_repo
from brain.src.utils.serialization import parse_object_id, serialize_doc


def get_knowledge_by_content_id(content_id: str, current_user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve machine-readable Knowledge extracted from a specific Content item (requires viewer role in space).
    """
    cid = parse_object_id(content_id, param_name="content_id")

    # Verify content item exists
    content_item = content_repo.get_content_item_by_id(cid)
    if not content_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content item with id '{content_id}' not found."
        )

    if current_user_id and content_item.get("space_id"):
        from brain.src.services.authorization import check_space_access
        check_space_access(str(content_item["space_id"]), current_user_id, required_role="viewer")

    knowledge_doc = knowledge_repo.get_knowledge_by_content_id(cid)
    if not knowledge_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No extracted knowledge found for content item '{content_id}'."
        )

    return serialize_doc(knowledge_doc)

