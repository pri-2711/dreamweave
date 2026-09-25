"""
Business logic service for Conversations and Messages.
"""

from typing import Dict, Any, List, Optional
from fastapi import HTTPException, status
from brain.src.database.repositories import conversations as conv_repo
from brain.src.database.repositories import spaces as spaces_repo
from brain.src.database.repositories import activity as activity_repo
from brain.src.schemas.conversations import ConversationCreate, MessageCreate
from brain.src.utils.serialization import parse_object_id, serialize_doc, serialize_docs


def create_conversation(space_id: str, data: ConversationCreate, current_user_id: str) -> Dict[str, Any]:
    """Create a new Space AI conversation."""
    sid = parse_object_id(space_id, param_name="space_id")
    space = spaces_repo.get_space_by_id(sid)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Space with id '{space_id}' not found."
        )

    uid = parse_object_id(current_user_id, param_name="user_id")
    doc = conv_repo.create_conversation(space_id=sid, user_id=uid, title=data.title.strip())

    return serialize_doc(doc)


def list_conversations(space_id: str) -> List[Dict[str, Any]]:
    """List conversations in a space."""
    sid = parse_object_id(space_id, param_name="space_id")
    conversations = conv_repo.list_conversations_by_space(sid)
    return serialize_docs(conversations)


def get_conversation(conversation_id: str) -> Dict[str, Any]:
    """Get conversation details by ID."""
    cid = parse_object_id(conversation_id, param_name="conversation_id")
    conv = conv_repo.get_conversation_by_id(cid)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with id '{conversation_id}' not found."
        )
    return serialize_doc(conv)


def add_message(conversation_id: str, data: MessageCreate, current_user_id: str) -> Dict[str, Any]:
    """Add a message to a conversation."""
    cid = parse_object_id(conversation_id, param_name="conversation_id")
    conv = conv_repo.get_conversation_by_id(cid)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with id '{conversation_id}' not found."
        )

    cnt_oids = [parse_object_id(i, param_name="content_id") for i in (data.content_ids or [])]
    knw_oids = [parse_object_id(i, param_name="knowledge_id") for i in (data.knowledge_ids or [])]
    gen_oids = [parse_object_id(i, param_name="generated_content_id") for i in (data.generated_content_ids or [])]

    doc = conv_repo.add_message(
        conversation_id=cid,
        role=data.role,
        content=data.content.strip(),
        content_ids=cnt_oids,
        knowledge_ids=knw_oids,
        generated_content_ids=gen_oids
    )

    return serialize_doc(doc)


def list_messages(conversation_id: str) -> List[Dict[str, Any]]:
    """List messages in a conversation."""
    cid = parse_object_id(conversation_id, param_name="conversation_id")
    conv = conv_repo.get_conversation_by_id(cid)
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with id '{conversation_id}' not found."
        )

    messages = conv_repo.list_messages_by_conversation(cid)
    return serialize_docs(messages)
