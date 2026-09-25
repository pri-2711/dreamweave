"""
Collection definitions for DreamWeave Database Architecture.
Defines constants and helper functions for accessing MongoDB collections.
"""

from typing import Dict
from pymongo.collection import Collection
from brain.src.database.connection import get_database

# 16 Conceptual Collections
COLLECTION_USERS = "users"
COLLECTION_SPACES = "spaces"
COLLECTION_SPACE_MEMBERS = "space_members"
COLLECTION_CONTENT_ITEMS = "content_items"
COLLECTION_ASSETS = "assets"
COLLECTION_KNOWLEDGE = "knowledge"
COLLECTION_CHUNKS = "chunks"
COLLECTION_AI_CONTENT = "ai_content"
COLLECTION_AI_GENERATIONS = "ai_generations"
COLLECTION_VISION_BOARDS = "vision_boards"
COLLECTION_VISION_BOARD_ITEMS = "vision_board_items"
COLLECTION_PLANS = "plans"
COLLECTION_TASKS = "tasks"
COLLECTION_CONVERSATIONS = "conversations"
COLLECTION_MESSAGES = "messages"
COLLECTION_ACTIVITY = "activity"

ALL_COLLECTIONS = [
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
]


def get_collection(name: str) -> Collection:
    """Get a PyMongo collection instance by name."""
    db = get_database()
    return db[name]


def get_all_collections() -> Dict[str, Collection]:
    """Return a dictionary of all 16 collections mapped to their PyMongo instances."""
    db = get_database()
    return {name: db[name] for name in ALL_COLLECTIONS}
