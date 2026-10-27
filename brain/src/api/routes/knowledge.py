"""
Knowledge API routes.
"""

from fastapi import APIRouter, Depends, status
from brain.src.api.deps import get_current_user_id
from brain.src import services

router = APIRouter(tags=["Knowledge"])


@router.get("/content/{content_id}/knowledge", status_code=status.HTTP_200_OK)
def get_content_knowledge(
    content_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Retrieve machine-readable Knowledge extracted from a specific Content item."""
    return services.knowledge_service.get_knowledge_by_content_id(content_id, current_user_id=current_user_id)

