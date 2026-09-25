"""
Embeddings Package for DreamWeave.
Exposes embedding services and text chunking utilities.
"""

from brain.src.embeddings.generator import EmbeddingGenerator, chunk_text
from brain.src.embeddings.service import embed_text, embed_documents

__all__ = ["EmbeddingGenerator", "chunk_text", "embed_text", "embed_documents"]
