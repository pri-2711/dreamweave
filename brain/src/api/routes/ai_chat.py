"""
Space-aware AI Chat API routes.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel, Field
from brain.src.api.deps import get_current_user_id
from brain.src.rag.service import answer_space_query
from brain.src.database.repositories import ai as ai_repo
from brain.src.utils.serialization import parse_object_id

router = APIRouter(tags=["AI Chat"])


class AIChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User question or prompt")
    top_k: Optional[int] = Field(default=None, description="Optional override for top-k RAG chunk retrieval")


@router.post("/spaces/{space_id}/ai/chat", status_code=status.HTTP_200_OK)
def space_ai_chat(
    space_id: str,
    payload: AIChatRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Space-aware AI Chat Endpoint:
    1. Retrieves top-k relevant knowledge chunks for the target Space.
    2. Builds grounded context prompt.
    3. Calls Gemini API service.
    4. Logs generation usage event to `ai_generations`.
    5. Returns grounded answer and source citations.
    """
    res = answer_space_query(space_id=space_id, question=payload.message, top_k=payload.top_k)

    # Log usage event to ai_generations collection
    uid = parse_object_id(current_user_id, param_name="user_id")
    sid = parse_object_id(space_id, param_name="space_id")
    ai_repo.create_ai_generation(
        user_id=uid,
        space_id=sid,
        type="chat",
        prompt=payload.message
    )

    return {
        "message": res["message"],
        "sources": res["sources"]
    }
