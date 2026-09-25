"""
Knowledge Ingestion Pipeline Service for DreamWeave.
Orchestrates: Content -> Extract -> Clean -> Knowledge -> Chunk -> Embed -> MongoDB.
"""

import os
import logging
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from brain.src.database.repositories import content as content_repo
from brain.src.database.repositories import assets as assets_repo
from brain.src.database.repositories import knowledge as knowledge_repo
from brain.src.database.repositories import chunks as chunks_repo
from brain.src.database.repositories import activity as activity_repo
from brain.src.extractors import image as image_extractor
from brain.src.extractors import pdf as pdf_extractor
from brain.src.cleaner import clean_document_content
from brain.src.chunking.service import chunk_knowledge_text
from brain.src.embeddings.service import embed_documents
from brain.src.utils.serialization import parse_object_id, serialize_doc

logger = logging.getLogger("dreamweave.services.ingestion")


def ingest_content_item(content_id: str, current_user_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Ingest a content item through the full AI knowledge pipeline:
    Content -> Extraction -> Cleaning -> Knowledge -> Chunking -> Embeddings -> MongoDB.
    """
    cid = parse_object_id(content_id, param_name="content_id")
    content_item = content_repo.get_content_item_by_id(cid)
    if not content_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Content item with id '{content_id}' not found."
        )

    space_id = content_item.get("space_id")
    user_id = content_item.get("user_id")
    item_type = content_item.get("type", "other")
    title = content_item.get("title", "")
    description = content_item.get("description", "")
    asset_id = content_item.get("asset_id")

    # Step 1: Extraction
    raw_text = ""
    ocr_used = False
    ocr_engine = None
    page_count = None

    asset_doc = assets_repo.get_asset_by_id(asset_id) if asset_id else None
    file_path = asset_doc.get("storage", {}).get("path") if asset_doc else None

    if file_path and os.path.exists(file_path):
        if item_type == "image":
            res = image_extractor.extract_text_from_image(file_path)
            raw_text = res.get("raw_text", "")
            ocr_used = res.get("ocr_used", False)
            ocr_engine = res.get("engine")
        elif item_type == "pdf":
            res = pdf_extractor.extract_text_from_pdf(file_path)
            raw_text = res.get("raw_text", "")
            ocr_used = res.get("ocr_used", False)
            ocr_engine = res.get("engine")
            page_count = res.get("pages")
    
    if not raw_text or not raw_text.strip():
        # Fallback to metadata text fields (notes, text, link titles/descriptions)
        parts = []
        if title:
            parts.append(title)
        if description:
            parts.append(description)
        preview = content_item.get("preview", {})
        if preview.get("title"):
            parts.append(preview["title"])
        if preview.get("description"):
            parts.append(preview["description"])
        raw_text = "\n\n".join(parts)

    if not raw_text or not raw_text.strip():
        raw_text = f"[Empty content item title: {title}]"

    # Step 2: Clean Text
    clean_text = clean_document_content(raw_text)

    # Step 3: Knowledge Document Store
    existing_k = knowledge_repo.get_knowledge_by_content_id(cid)
    if existing_k:
        knowledge_repo.update_knowledge(existing_k["_id"], {
            "raw_text": raw_text,
            "clean_text": clean_text,
            "metadata.ocr_used": ocr_used,
            "metadata.page_count": page_count,
            "metadata.ocr_engine": ocr_engine
        })
        knowledge_doc = knowledge_repo.get_knowledge_by_id(existing_k["_id"])
    else:
        knowledge_doc = knowledge_repo.create_knowledge(
            space_id=space_id,
            content_id=cid,
            source_type=item_type,
            raw_text=raw_text,
            clean_text=clean_text,
            ocr_used=ocr_used,
            page_count=page_count,
            ocr_engine=ocr_engine
        )

    knowledge_id = knowledge_doc["_id"]

    # Step 4: Chunking
    chunk_objs = chunk_knowledge_text(clean_text)

    # Step 5: Embeddings
    chunk_texts = [c["text"] for c in chunk_objs]
    embeddings = embed_documents(chunk_texts)

    # Step 6: Store Chunks & Vector Embeddings in MongoDB `chunks` collection
    from brain.src.database.collections import COLLECTION_CHUNKS, get_collection
    coll_chunks = get_collection(COLLECTION_CHUNKS)
    # Remove older chunks for this knowledge entry to ensure clean re-ingestion
    coll_chunks.delete_many({"knowledge_id": knowledge_id})

    created_chunk_docs = []
    for idx, c_obj in enumerate(chunk_objs):
        emb = embeddings[idx] if idx < len(embeddings) else []
        c_doc = chunks_repo.create_chunk(
            space_id=space_id,
            knowledge_id=knowledge_id,
            content_id=cid,
            chunk_index=c_obj["chunk_index"],
            text=c_obj["text"],
            embedding=emb
        )
        created_chunk_docs.append(c_doc)

    # Log activity
    if space_id and user_id:
        activity_repo.log_activity(
            space_id=space_id,
            user_id=user_id,
            action="content_ingested",
            target_type="content_item",
            target_id=cid
        )

    return {
        "status": "ok",
        "content_id": str(cid),
        "knowledge_id": str(knowledge_id),
        "chunks_count": len(created_chunk_docs),
        "ocr_used": ocr_used,
        "knowledge": serialize_doc(knowledge_doc)
    }
