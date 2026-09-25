"""
Knowledge API routes.
"""

from fastapi import APIRouter, status
from brain.src import services

router = APIRouter(tags=["Knowledge"])


@router.get("/content/{content_id}/knowledge", status_code=status.HTTP_200_OK)
def get_content_knowledge(content_id: str):
    """Retrieve machine-readable Knowledge extracted from a specific Content item."""
    return services.knowledge_service.get_knowledge_by_content_id(content_id)
