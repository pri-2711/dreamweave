import re
import numpy as np
from typing import List, Dict, Any


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
    """
    Split text into overlapping semantic chunks for embedding generation.
    Respects paragraph and sentence boundaries where possible.
    """
    if not text or not text.strip():
        return []

    # Split by paragraphs first
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                chunks.append(current_chunk)
            # If paragraph itself is longer than chunk_size, split by sentences
            if len(para) > chunk_size:
                sentences = re.split(r'(?<=[.!?])\s+', para)
                sub_chunk = ""
                for sent in sentences:
                    if len(sub_chunk) + len(sent) + 1 <= chunk_size:
                        sub_chunk = (sub_chunk + " " + sent).strip()
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = sent
                if sub_chunk:
                    current_chunk = sub_chunk
            else:
                current_chunk = para

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


class EmbeddingGenerator:
    """
    Vector Embedding Generator supporting TF-IDF vector features and dense normalized vectors.
    """

    def __init__(self):
        self.vectorizer = None

    def fit_transform_corpus(self, texts: List[str]) -> List[List[float]]:
        """
        Fits vectorizer on the given corpus of texts and converts texts into dense vector arrays.
        """
        if not texts:
            return []

        from sklearn.feature_extraction.text import TfidfVectorizer

        self.vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            max_features=512,
            stop_words='english',
            sublinear_tf=True
        )

        matrix = self.vectorizer.fit_transform(texts).toarray()
        # L2 Normalize vectors
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        normalized_matrix = matrix / norms
        return normalized_matrix.tolist()

    def transform_query(self, query: str) -> List[float]:
        """
        Transforms a query string into vector space using fitted vectorizer.
        """
        if not self.vectorizer:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=512)
            self.vectorizer.fit([query])

        try:
            vec = self.vectorizer.transform([query]).toarray()
        except Exception:
            vec = self.vectorizer.fit_transform([query]).toarray()

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec[0].tolist()

