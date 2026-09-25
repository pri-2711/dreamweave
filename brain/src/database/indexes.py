"""
Programmatic index creation for DreamWeave Database Architecture.
Ensures all required indexes exist in MongoDB Atlas idempotently.
"""

import logging
from typing import Dict, List, Any
from pymongo import ASCENDING, DESCENDING
from brain.src.database.connection import get_database
from brain.src.database.collections import (
    COLLECTION_USERS,
    COLLECTION_SPACES,
    COLLECTION_SPACE_MEMBERS,
    COLLECTION_CONTENT_ITEMS,
    COLLECTION_ASSETS,
    COLLECTION_KNOWLEDGE,
    COLLECTION_CHUNKS,
    COLLECTION_AI_CONTENT,
    COLLECTION_AI_GENERATIONS,
    COLLECTION_VISION_BOARDS,
    COLLECTION_VISION_BOARD_ITEMS,
    COLLECTION_PLANS,
    COLLECTION_TASKS,
    COLLECTION_CONVERSATIONS,
    COLLECTION_MESSAGES,
    COLLECTION_ACTIVITY,
)

logger = logging.getLogger("dreamweave.database.indexes")

# Index Specifications according to DreamWeave Architecture
INDEX_SPECS: Dict[str, List[Dict[str, Any]]] = {
    COLLECTION_USERS: [
        {"keys": [("email", ASCENDING)], "unique": True},
    ],
    COLLECTION_SPACES: [
        {"keys": [("owner_id", ASCENDING)]},
        {"keys": [("owner_id", ASCENDING), ("status", ASCENDING)]},
    ],
    COLLECTION_SPACE_MEMBERS: [
        {"keys": [("space_id", ASCENDING)]},
        {"keys": [("user_id", ASCENDING)]},
        {"keys": [("space_id", ASCENDING), ("user_id", ASCENDING)], "unique": True},
    ],
    COLLECTION_CONTENT_ITEMS: [
        {"keys": [("space_id", ASCENDING)]},
        {"keys": [("user_id", ASCENDING)]},
        {"keys": [("type", ASCENDING)]},
        {"keys": [("created_at", DESCENDING)]},
        {"keys": [("space_id", ASCENDING), ("organization.is_favourite", ASCENDING)]},
        {"keys": [("space_id", ASCENDING), ("organization.is_archived", ASCENDING)]},
    ],
    COLLECTION_ASSETS: [
        {"keys": [("content_id", ASCENDING)]},
        {"keys": [("space_id", ASCENDING)]},
        {"keys": [("user_id", ASCENDING)]},
    ],
    COLLECTION_KNOWLEDGE: [
        {"keys": [("space_id", ASCENDING)]},
        {"keys": [("content_id", ASCENDING)]},
    ],
    COLLECTION_CHUNKS: [
        {"keys": [("space_id", ASCENDING)]},
        {"keys": [("knowledge_id", ASCENDING)]},
        {"keys": [("content_id", ASCENDING)]},
    ],
    COLLECTION_AI_CONTENT: [
        {"keys": [("space_id", ASCENDING)]},
        {"keys": [("user_id", ASCENDING)]},
        {"keys": [("type", ASCENDING)]},
        {"keys": [("created_at", DESCENDING)]},
    ],
    COLLECTION_AI_GENERATIONS: [
        {"keys": [("user_id", ASCENDING)]},
        {"keys": [("type", ASCENDING)]},
        {"keys": [("created_at", DESCENDING)]},
        {"keys": [("user_id", ASCENDING), ("type", ASCENDING), ("created_at", DESCENDING)]},
    ],
    COLLECTION_VISION_BOARDS: [
        {"keys": [("space_id", ASCENDING)]},
    ],
    COLLECTION_VISION_BOARD_ITEMS: [
        {"keys": [("vision_board_id", ASCENDING)]},
        {"keys": [("content_id", ASCENDING)]},
    ],
    COLLECTION_PLANS: [
        {"keys": [("space_id", ASCENDING)]},
        {"keys": [("user_id", ASCENDING)]},
    ],
    COLLECTION_TASKS: [
        {"keys": [("plan_id", ASCENDING)]},
        {"keys": [("space_id", ASCENDING)]},
        {"keys": [("status", ASCENDING)]},
    ],
    COLLECTION_CONVERSATIONS: [
        {"keys": [("space_id", ASCENDING)]},
        {"keys": [("user_id", ASCENDING)]},
    ],
    COLLECTION_MESSAGES: [
        {"keys": [("conversation_id", ASCENDING)]},
        {"keys": [("created_at", ASCENDING)]},
    ],
    COLLECTION_ACTIVITY: [
        {"keys": [("space_id", ASCENDING)]},
        {"keys": [("user_id", ASCENDING)]},
        {"keys": [("created_at", DESCENDING)]},
    ],
}


def ensure_indexes(db=None) -> Dict[str, List[str]]:
    """
    Programmatically create all indexes across the 16 conceptual collections.
    Can be run safely multiple times (idempotent).
    Returns a dict mapping collection names to list of index names.
    """
    if db is None:
        db = get_database()

    results = {}
    for coll_name, specs in INDEX_SPECS.items():
        collection = db[coll_name]
        created_for_coll = []
        for spec in specs:
            keys = spec["keys"]
            unique = spec.get("unique", False)
            try:
                index_name = collection.create_index(keys, unique=unique)
                created_for_coll.append(index_name)
                logger.debug(f"Index '{index_name}' ensured for collection '{coll_name}'")
            except Exception as e:
                logger.error(f"Failed creating index {keys} on '{coll_name}': {e}")
                created_for_coll.append(f"ERROR: {e}")
        results[coll_name] = created_for_coll

    logger.info(f"Ensured indexes for {len(results)} collections.")
    return results
