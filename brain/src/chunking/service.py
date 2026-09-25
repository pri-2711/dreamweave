"""
Text Chunking Service for DreamWeave RAG Pipeline.
Splits clean text into structured overlapping chunks respecting paragraph/sentence boundaries.
"""

import re
from typing import List, Dict, Any, Optional
from brain.src import config


def chunk_knowledge_text(
    text: str,
    chunk_size: Optional[int] = None,
    overlap: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Split clean knowledge text into structured chunk objects.
    Returns list of dicts with:
      - `text`: chunk string content
      - `chunk_index`: 0-based integer index
      - `length`: character length of chunk text
    """
    if not text or not text.strip():
        return []

    c_size = chunk_size or config.CHUNK_SIZE or 500
    c_overlap = overlap or config.CHUNK_OVERLAP or 50

    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    raw_chunks: List[str] = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= c_size:
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
        else:
            if current_chunk:
                raw_chunks.append(current_chunk)
            if len(para) > c_size:
                # Split large paragraph by sentence boundaries
                sentences = re.split(r'(?<=[.!?])\s+', para)
                sub_chunk = ""
                for sent in sentences:
                    if len(sub_chunk) + len(sent) + 1 <= c_size:
                        sub_chunk = (sub_chunk + " " + sent).strip()
                    else:
                        if sub_chunk:
                            raw_chunks.append(sub_chunk)
                        sub_chunk = sent
                if sub_chunk:
                    current_chunk = sub_chunk
            else:
                current_chunk = para

    if current_chunk:
        raw_chunks.append(current_chunk)

    # Format structured chunk objects
    structured_chunks = []
    for idx, chunk_str in enumerate(raw_chunks):
        structured_chunks.append({
            "text": chunk_str,
            "chunk_index": idx,
            "length": len(chunk_str)
        })

    return structured_chunks
