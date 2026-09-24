import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient

# Configure logger
logger = logging.getLogger("dreamweave.database")

# Load environment variables from both workspace root .env and brain/.env if present
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

_client = None


def get_mongo_uri() -> str:
    uri = os.getenv("MONGODB_URI")
    if not uri or not uri.strip():
        raise ValueError("MONGODB_URI environment variable is not set.")
    return uri.strip()


def get_database_name() -> str:
    return os.getenv("MONGODB_DATABASE", "dreamweave").strip()


def get_mongo_client() -> MongoClient:
    global _client
    if _client is None:
        uri = get_mongo_uri()
        kwargs = {"serverSelectionTimeoutMS": 5000}
        try:
            import certifi
            kwargs["tlsCAFile"] = certifi.where()
        except ImportError:
            pass
        _client = MongoClient(uri, **kwargs)
    return _client



def get_database():
    client = get_mongo_client()
    db_name = get_database_name()
    return client[db_name]


def ping_database():
    """
    Ping MongoDB server to verify active connection.
    Returns dict status on success or raises Exception on failure.
    """
    client = get_mongo_client()
    # Ping admin command
    client.admin.command("ping")
    return {
        "status": "ok",
        "database": get_database_name()
    }
