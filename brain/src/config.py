"""
Central Configuration for DreamWeave Brain.
Loads environment variables for Gemini API, Embedding models, chunking, and RAG.
"""

import os
from dotenv import load_dotenv

# Load environment variables from workspace root and brain directory
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

# Gemini API Configuration
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-1.5-flash").strip()

# Embedding Model Configuration
# Selected pretrained lightweight model: BAAI/bge-small-en-v1.5 (or all-MiniLM-L6-v2)
EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5").strip()
EMBEDDING_DIMENSION: int = 384

# RAG & Chunking Configuration
CHUNK_SIZE: int = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP: int = int(os.getenv("CHUNK_OVERLAP", "50"))
RAG_TOP_K: int = int(os.getenv("RAG_TOP_K", "5"))
