import numpy as np
from typing import List, Dict, Any
from brain.src.vector_store import load_vector_store, compute_cosine_similarity
from brain.src.embeddings.generator import EmbeddingGenerator


def retrieve_relevant_chunks(query: str, top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Given a search query, search the vector store for top_k relevant document chunks.
    Returns list of dicts with chunk text, metadata, doc_id, filename, score.
    """
    if not query or not query.strip():
        return []

    store_data = load_vector_store()
    chunks = store_data.get("chunks", [])
    vocab = store_data.get("vocabulary", {})

    if not chunks:
        return []

    # Reconstruct vectorizer with stored vocabulary
    from sklearn.feature_extraction.text import TfidfVectorizer
    generator = EmbeddingGenerator()

    if vocab:
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=512, stop_words='english', vocabulary=vocab)
        vectorizer.fit(list(vocab.keys()))
        generator.vectorizer = vectorizer
        query_vec = generator.transform_query(query)
    else:

        # Fallback: simple character/word overlap vector
        query_words = set(query.lower().split())
        query_vec = None

    scored_chunks = []

    for chunk in chunks:
        chunk_vec = chunk.get("vector", [])
        if query_vec and chunk_vec:
            score = compute_cosine_similarity(query_vec, chunk_vec)
        else:
            # Word-level fallback scoring if vectors empty
            chunk_text = chunk.get("text", "").lower()
            chunk_words = set(chunk_text.split())
            if not chunk_words or not query_words:
                score = 0.0
            else:
                intersection = query_words.intersection(chunk_words)
                score = len(intersection) / float(len(query_words))

        if score > 0.0:
            scored_chunks.append({
                "chunk_id": chunk.get("chunk_id"),
                "doc_id": chunk.get("doc_id"),
                "filename": chunk.get("filename"),
                "source": chunk.get("source"),
                "text": chunk.get("text"),
                "score": score
            })

    # Sort descending by similarity score
    scored_chunks.sort(key=lambda x: x["score"], reverse=True)
    return scored_chunks[:top_k]
