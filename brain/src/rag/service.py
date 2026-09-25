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
    top_k: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform Space-aware grounded RAG query:
    1. Validate space_id.
    2. Embed question into 384-dimensional vector space.
    3. Retrieve top-k relevant chunks filtered strictly by space_id.
    4. Build grounded RAG prompt.
    5. Call Gemini API service.
    6. Return answer with source references.
    """
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
