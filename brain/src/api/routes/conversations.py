"""
Conversations and Messages API routes.
"""

from fastapi import APIRouter, Depends, status
from brain.src.api.deps import get_current_user_id
from brain.src.schemas.conversations import ConversationCreate, MessageCreate
from brain.src import services

router = APIRouter(tags=["Conversations & Messages"])


# --- Conversation Routes ---

@router.post("/spaces/{space_id}/conversations", status_code=status.HTTP_201_CREATED)
def create_conversation(
    space_id: str,
    payload: ConversationCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create a new Space AI conversation."""
    return services.conversations_service.create_conversation(space_id, payload, current_user_id)


@router.get("/spaces/{space_id}/conversations", status_code=status.HTTP_200_OK)
def list_conversations(space_id: str):
    """List conversations in a space."""
    return services.conversations_service.list_conversations(space_id)


@router.get("/conversations/{conversation_id}", status_code=status.HTTP_200_OK)
def get_conversation(conversation_id: str):
    """Get conversation details by ID."""
    return services.conversations_service.get_conversation(conversation_id)


# --- Message Routes ---

@router.post("/conversations/{conversation_id}/messages", status_code=status.HTTP_201_CREATED)
def add_message(
    conversation_id: str,
    payload: MessageCreate,
    current_user_id: str = Depends(get_current_user_id)
):
    """Add a message to a conversation."""
    return services.conversations_service.add_message(conversation_id, payload, current_user_id)


@router.get("/conversations/{conversation_id}/messages", status_code=status.HTTP_200_OK)
def list_messages(conversation_id: str):
    """List all messages in a conversation."""
    return services.conversations_service.list_messages(conversation_id)
