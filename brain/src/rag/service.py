"""
RAG Service for DreamWeave.
Orchestrates vector embedding, Space-scoped retrieval, prompt grounding, and Gemini AI response generation.
"""

import logging
from typing import Dict, Any, List, Optional
from brain.src import config
from brain.src.database.repositories import spaces as spaces_repo
from brain.src.database.repositories import content as content_repo
from brain.src.embeddings.service import embed_text
from brain.src.rag.retriever import retrieve_space_chunks
from brain.src.rag.prompt_builder import build_grounded_rag_prompt
from brain.src.ai.gemini import generate_gemini_response
from brain.src.utils.serialization import parse_object_id

logger = logging.getLogger("dreamweave.rag.service")


def answer_space_query(
    space_id: str,
    question: str,
    top_k: Optional[int] = None,
    current_user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform Space-aware grounded RAG query:
    1. Validate space_id and check viewer permission.
    2. Embed question into 384-dimensional vector space.
    3. Retrieve top-k relevant chunks filtered strictly by space_id.
    4. Build grounded RAG prompt.
    5. Call Gemini API service.
    6. Return answer with source references.
    """
    if current_user_id:
        from brain.src.services.authorization import check_space_access
        check_space_access(space_id, current_user_id, required_role="viewer")

    sid = parse_object_id(space_id, param_name="space_id")
    space = spaces_repo.get_space_by_id(sid)
    space_name = space.get("name") if space else None


    k = top_k or config.RAG_TOP_K or 5

    # Step 1: Embed question
    query_embedding = embed_text(question)

    # Step 2: Retrieve Space-scoped chunks
    chunks = retrieve_space_chunks(space_id=space_id, query_embedding=query_embedding, top_k=k)

    # Step 3: Build Grounded Prompt
    prompt_payload = build_grounded_rag_prompt(
        question=question,
        retrieved_chunks=chunks,
        space_name=space_name
    )

    # Step 4: Generate Response via Gemini Service
    answer_text = generate_gemini_response(
        prompt=prompt_payload["prompt"],
        system_instruction=prompt_payload["system_instruction"]
    )

    # Step 5: Format Source References
    sources = []
    seen_content_ids = set()
    for c in chunks:
        cid = c.get("content_id")
        if cid and cid not in seen_content_ids:
            seen_content_ids.add(cid)
            content_doc = content_repo.get_content_item_by_id(cid)
            sources.append({
                "content_id": cid,
                "title": content_doc.get("title") if content_doc else None,
                "type": content_doc.get("type") if content_doc else None,
                "score": round(c.get("score", 0.0), 3)
            })

    return {
        "space_id": space_id,
        "question": question,
        "message": answer_text,
        "sources": sources,
        "chunks": chunks
    }


def answer_conversation_query(
    conversation_id: str,
    message: str,
    top_k: Optional[int] = None,
    current_user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Perform conversational RAG query inside a specific conversation:
    1. Look up conversation and verify space permissions.
    2. Embed user message and retrieve space-scoped chunks.
    3. Retrieve conversation message history.
    4. Build conversation RAG prompt.
    5. Generate Gemini assistant response.
    6. Save assistant message with citations into conversation messages.
    7. Return formatted response with assistant message and citations.
    """
    from brain.src.database.repositories import conversations as conv_repo
    from brain.src.rag.prompt_builder import build_conversation_rag_prompt

    cid = parse_object_id(conversation_id, param_name="conversation_id")
    conv = conv_repo.get_conversation_by_id(cid)
    if not conv:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Conversation with id '{conversation_id}' not found."
        )

    space_id = str(conv["space_id"])
    if current_user_id:
        from brain.src.services.authorization import check_space_access
        check_space_access(space_id, current_user_id, required_role="editor")

    space = spaces_repo.get_space_by_id(conv["space_id"])
    space_name = space.get("name") if space else None

    # Step 1: Embed question
    k = top_k or config.RAG_TOP_K or 5
    query_embedding = embed_text(message)

    # Step 2: Retrieve Space-scoped chunks
    chunks = retrieve_space_chunks(space_id=space_id, query_embedding=query_embedding, top_k=k)

    # Step 3: Get prior messages
    history_messages = conv_repo.list_messages_by_conversation(cid)

    # Step 4: Build grounded conversation prompt
    prompt_payload = build_conversation_rag_prompt(
        messages=history_messages,
        new_message=message,
        retrieved_chunks=chunks,
        space_name=space_name
    )

    # Step 5: Generate AI response
    answer_text = generate_gemini_response(
        prompt=prompt_payload["prompt"],
        system_instruction=prompt_payload["system_instruction"]
    )

    # Step 6: Identify source content references
    sources = []
    seen_content_ids = set()
    source_content_oids = []
    for c in chunks:
        c_id = c.get("content_id")
        if c_id and c_id not in seen_content_ids:
            seen_content_ids.add(c_id)
            content_doc = content_repo.get_content_item_by_id(c_id)
            source_content_oids.append(parse_object_id(c_id))
            sources.append({
                "content_id": c_id,
                "title": content_doc.get("title") if content_doc else None,
                "type": content_doc.get("type") if content_doc else None,
                "score": round(c.get("score", 0.0), 3)
            })

    # Step 7: Record assistant message in conversation
    assistant_msg_doc = conv_repo.add_message(
        conversation_id=cid,
        role="assistant",
        content=answer_text,
        content_ids=source_content_oids
    )

    from brain.src.utils.serialization import serialize_doc
    return {
        "conversation_id": conversation_id,
        "space_id": space_id,
        "message": serialize_doc(assistant_msg_doc),
        "answer": answer_text,
        "sources": sources
    }


def generate_space_content(
    space_id: str,
    prompt: str,
    content_type: str = "suggestion",
    title: Optional[str] = None,
    save_to_space: bool = True,
    current_user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate AI content (itinerary, summary, suggestion, checklist) grounded in Space knowledge.
    Optionally persists the result to `ai_content` collection.
    """
    from brain.src.rag.prompt_builder import build_content_generation_prompt

    if current_user_id:
        from brain.src.services.authorization import check_space_access
        check_space_access(space_id, current_user_id, required_role="editor")

    sid = parse_object_id(space_id, param_name="space_id")
    space = spaces_repo.get_space_by_id(sid)
    space_name = space.get("name") if space else None

    # Step 1: Embed prompt to retrieve relevant space items
    query_embedding = embed_text(prompt)
    chunks = retrieve_space_chunks(space_id=space_id, query_embedding=query_embedding, top_k=config.RAG_TOP_K or 5)

    # Step 2: Build generation prompt
    prompt_payload = build_content_generation_prompt(
        prompt=prompt,
        generation_type=content_type,
        retrieved_chunks=chunks,
        space_name=space_name
    )

    # Step 3: Call Gemini AI
    generated_text = generate_gemini_response(
        prompt=prompt_payload["prompt"],
        system_instruction=prompt_payload["system_instruction"]
    )

    sources = []
    seen_content_ids = set()
    source_content_oids = []
    for c in chunks:
        c_id = c.get("content_id")
        if c_id and c_id not in seen_content_ids:
            seen_content_ids.add(c_id)
            content_doc = content_repo.get_content_item_by_id(c_id)
            source_content_oids.append(parse_object_id(c_id))
            sources.append({
                "content_id": c_id,
                "title": content_doc.get("title") if content_doc else None,
                "type": content_doc.get("type") if content_doc else None
            })

    # Step 4: Persist to ai_content if requested
    persisted_doc = None
    if save_to_space:
        from brain.src.database.repositories import ai as ai_repo
        from brain.src.utils.serialization import serialize_doc
        uid = parse_object_id(current_user_id, param_name="user_id") if current_user_id else sid
        persisted_doc = ai_repo.create_ai_content(
            space_id=sid,
            user_id=uid,
            type=content_type,
            content=generated_text,
            title=title or f"AI {content_type.capitalize()}",
            source_content_ids=source_content_oids
        )
        persisted_doc = serialize_doc(persisted_doc)

    return {
        "space_id": space_id,
        "type": content_type,
        "content": generated_text,
        "title": title or f"AI {content_type.capitalize()}",
        "sources": sources,
        "saved_item": persisted_doc
    }

