"""
Embedding Service for DreamWeave.
Loads pretrained embedding model (BAAI/bge-small-en-v1.5, 384 dimensions)
and produces L2-normalized vector embeddings for text and bulk chunks.
"""

import logging
import numpy as np
from typing import List
from brain.src import config

logger = logging.getLogger("dreamweave.embeddings")

_fastembed_model = None


def _get_embedding_model():
    """Lazy initialization of FastEmbed ONNX embedding model."""
    global _fastembed_model
    if _fastembed_model is None:
        try:
            from fastembed import TextEmbedding
            model_name = config.EMBEDDING_MODEL_NAME or "BAAI/bge-small-en-v1.5"
            logger.info(f"Loading pretrained FastEmbed model '{model_name}'...")
            _fastembed_model = TextEmbedding(model_name=model_name)
        except Exception as e:
            logger.warning(f"FastEmbed load warning ({e}). Trying SentenceTransformer fallback...")
            try:
                from sentence_transformers import SentenceTransformer
                _fastembed_model = SentenceTransformer(config.EMBEDDING_MODEL_NAME or "all-MiniLM-L6-v2")
            except Exception as st_e:
                logger.error(f"Embedding model load failed: {st_e}")
                _fastembed_model = None
    return _fastembed_model


def embed_text(text: str) -> List[float]:
    """
    Generate a 384-dimensional normalized vector embedding for a single text string.
    """
    if not text or not text.strip():
        return [0.0] * config.EMBEDDING_DIMENSION

    model = _get_embedding_model()
    if model:
        try:
            if hasattr(model, "embed"):
                # FastEmbed API
                embeddings = list(model.embed([text.strip()]))
                vec = embeddings[0].tolist()
            elif hasattr(model, "encode"):
                # SentenceTransformer API
                vec = model.encode(text.strip()).tolist()
            else:
                vec = None

            if vec:
                # Ensure 384 dimension padding/truncation if needed
                if len(vec) != config.EMBEDDING_DIMENSION:
                    vec = _align_dimension(vec, config.EMBEDDING_DIMENSION)
                return _normalize_vector(vec)
        except Exception as e:
            logger.error(f"Failed generating vector embedding: {e}")

    # Heuristic fallback generator (deterministic 384-dim normalized pseudo-vector)
    return _heuristic_vector(text, config.EMBEDDING_DIMENSION)


def embed_documents(texts: List[str]) -> List[List[float]]:
    """
    Generate vector embeddings for a list of document chunk text strings.
    """
    if not texts:
        return []

    clean_texts = [t.strip() for t in texts]
    model = _get_embedding_model()

    if model:
        try:
            if hasattr(model, "embed"):
                raw_embeddings = list(model.embed(clean_texts))
                return [_normalize_vector(_align_dimension(vec.tolist(), config.EMBEDDING_DIMENSION)) for vec in raw_embeddings]
            elif hasattr(model, "encode"):
                raw_embeddings = model.encode(clean_texts)
                return [_normalize_vector(_align_dimension(vec.tolist(), config.EMBEDDING_DIMENSION)) for vec in raw_embeddings]
        except Exception as e:
            logger.error(f"Bulk embedding generation failed: {e}")

    return [embed_text(t) for t in clean_texts]


def _align_dimension(vec: List[float], target_dim: int) -> List[float]:
    """Ensure vector matches target dimension exactly."""
    if len(vec) == target_dim:
        return vec
    elif len(vec) > target_dim:
        return vec[:target_dim]
    else:
        return vec + [0.0] * (target_dim - len(vec))


def _normalize_vector(vec: List[float]) -> List[float]:
    """L2 normalize a floating point vector."""
    arr = np.array(vec, dtype=float)
    norm = np.linalg.norm(arr)
    if norm == 0:
        return vec
    return (arr / norm).tolist()


def _heuristic_vector(text: str, dim: int = 384) -> List[float]:
    """Deterministic 384-dimensional normalized hashing vector fallback."""
    vec = [0.0] * dim
    words = text.lower().split()
    for w in words:
        idx = hash(w) % dim
        vec[idx] += 1.0
    return _normalize_vector(vec)
