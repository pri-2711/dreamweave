"""
DreamWeave Brain Database Package.
"""

from brain.src.database.connection import (
    get_mongo_client,
    get_database,
    ping_database,
    init_database
)
from brain.src.database.collections import (
    ALL_COLLECTIONS,
    get_collection,
    get_all_collections
)
from brain.src.database.indexes import ensure_indexes

__all__ = [
    "get_mongo_client",
    "get_database",
    "ping_database",
    "init_database",
    "ALL_COLLECTIONS",
    "get_collection",
    "get_all_collections",
    "ensure_indexes",
]
