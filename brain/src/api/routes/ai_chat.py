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
    res = answer_space_query(
        space_id=space_id,
        question=payload.message,
        top_k=payload.top_k,
        current_user_id=current_user_id
    )

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


class ConversationChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="User question or prompt in conversation")
    top_k: Optional[int] = Field(default=None, description="Optional override for top-k RAG chunk retrieval")


@router.post("/conversations/{conversation_id}/chat", status_code=status.HTTP_200_OK)
def conversation_chat(
    conversation_id: str,
    payload: ConversationChatRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Multi-turn Conversational AI Chat Endpoint:
    1. Records user message in the conversation.
    2. Runs grounded Space-scoped RAG with previous conversation context.
    3. Calls Gemini API service.
    4. Records assistant reply in the conversation.
    5. Returns assistant reply, source citations, and message metadata.
    """
    from brain.src.services.conversations_service import add_message
    from brain.src.schemas.conversations import MessageCreate
    from brain.src.rag.service import answer_conversation_query

    # Step 1: Record user message
    add_message(
        conversation_id=conversation_id,
        data=MessageCreate(role="user", content=payload.message),
        current_user_id=current_user_id
    )

    # Step 2: Generate grounded RAG reply with history
    res = answer_conversation_query(
        conversation_id=conversation_id,
        message=payload.message,
        top_k=payload.top_k,
        current_user_id=current_user_id
    )

    # Step 3: Record usage event
    uid = parse_object_id(current_user_id, param_name="user_id")
    sid = parse_object_id(res["space_id"], param_name="space_id")
    ai_repo.create_ai_generation(
        user_id=uid,
        space_id=sid,
        type="conversation_chat",
        prompt=payload.message
    )

    return res


class AIGenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Generation instruction or prompt")
    type: str = Field(default="suggestion", description="Content type: itinerary, summary, suggestion, checklist")
    title: Optional[str] = Field(default=None, description="Optional custom title for generated item")
    save_to_space: bool = Field(default=True, description="Whether to save directly to Space ai_content collection")


@router.post("/spaces/{space_id}/ai/generate", status_code=status.HTTP_201_CREATED)
def space_ai_generate(
    space_id: str,
    payload: AIGenerateRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    AI Content Generation Endpoint:
    1. Retrieves relevant Space knowledge items based on the prompt.
    2. Builds structured content generation prompt.
    3. Calls Gemini AI service.
    4. Automatically saves generated output into `ai_content` when save_to_space=True.
    5. Records generation usage event in `ai_generations`.
    """
    from brain.src.rag.service import generate_space_content

    res = generate_space_content(
        space_id=space_id,
        prompt=payload.prompt,
        content_type=payload.type,
        title=payload.title,
        save_to_space=payload.save_to_space,
        current_user_id=current_user_id
    )

    # Record usage event
    uid = parse_object_id(current_user_id, param_name="user_id")
    sid = parse_object_id(space_id, param_name="space_id")
    ai_repo.create_ai_generation(
        user_id=uid,
        space_id=sid,
        type=payload.type,
        prompt=payload.prompt
    )

    return res

