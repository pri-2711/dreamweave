import json
import os
import numpy as np
from typing import List, Dict, Any
from brain.src.document_store import get_all_documents
from brain.src.embeddings.generator import EmbeddingGenerator, chunk_text

VECTOR_FILE = "brain/data/vectors.json"


def _ensure_vector_store_exists():
    os.makedirs(os.path.dirname(VECTOR_FILE), exist_ok=True)
    if not os.path.exists(VECTOR_FILE):
        with open(VECTOR_FILE, "w", encoding="utf-8") as f:
            json.dump({"chunks": [], "vectorizer_vocabulary": {}}, f)


def save_vector_store(chunks: List[Dict[str, Any]], vocabulary: Dict[str, int]):
    """Save chunk vectors and vocabulary metadata into local JSON vector store."""
    _ensure_vector_store_exists()
    store_data = {
        "chunks": chunks,
        "vocabulary": vocabulary
    }
    with open(VECTOR_FILE, "w", encoding="utf-8") as f:
        json.dump(store_data, f, indent=4, ensure_ascii=False)


def load_vector_store() -> Dict[str, Any]:
    """Load vector store data from disk."""
    _ensure_vector_store_exists()
    with open(VECTOR_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {"chunks": [], "vocabulary": {}}


def build_vector_index():
    """
    Ingest all documents from knowledge base, chunk content, generate vector embeddings,
    and persist into local vector store.
    """
    documents = get_all_documents()
    if not documents:
        print("No documents found in knowledge base to index.")
        return 0

    all_chunks_info = []
    corpus_texts = []

    for doc in documents:
        doc_id = doc.get("id")
        filename = doc.get("filename", "")
        source = doc.get("source", "")
        # Prefer clean_content, fallback to raw_content
        content = doc.get("clean_content") or doc.get("raw_content", "")

        if not content or not content.strip():
            continue

        text_chunks = chunk_text(content)
        for idx, chunk_str in enumerate(text_chunks):
            corpus_texts.append(chunk_str)
            all_chunks_info.append({
                "chunk_id": f"{doc_id}_chunk_{idx}",
                "doc_id": doc_id,
                "filename": filename,
                "source": source,
                "chunk_index": idx,
                "text": chunk_str,
                "vector": []
            })

    if not corpus_texts:
        print("No valid text content found to generate vectors.")
        return 0

    generator = EmbeddingGenerator()
    vectors = generator.fit_transform_corpus(corpus_texts)

    for i, vec in enumerate(vectors):
        all_chunks_info[i]["vector"] = vec

    vocab = {}
    if generator.vectorizer and hasattr(generator.vectorizer, "vocabulary_"):
        # Store vocabulary mapping (word -> feature index) as int
        vocab = {k: int(v) for k, v in generator.vectorizer.vocabulary_.items()}

    save_vector_store(all_chunks_info, vocab)
    print(f"Successfully generated vector index for {len(all_chunks_info)} text chunks across {len(documents)} documents.")
    return len(all_chunks_info)


def compute_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    a = np.array(vec1, dtype=float)
    b = np.array(vec2, dtype=float)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))
