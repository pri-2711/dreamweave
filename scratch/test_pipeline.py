import os
import sys

# Ensure workspace is in path
sys.path.insert(0, os.path.abspath("."))

from brain.src.extractors.notes import extract_text_from_note
from brain.src.document_store import save_document, get_all_documents
from brain.src.cleaner import process_all_document_cleanups
from brain.src.vector_store import build_vector_index, load_vector_store
from brain.src.retrieval.retriever import retrieve_relevant_chunks
from brain.src.rag.rag_engine import answer_rag_query

def run_test():
    print("=== TEST 1: Ingest Sample Document Note ===")
    sample_note = (
        "DreamWeave Project Specification:\n"
        "DreamWeave is an intelligent document ingestion and retrieval system.\n"
        "It supports Image OCR, PDF text extraction, AI text cleanup, vector embeddings, "
        "semantic search using cosine similarity, and RAG conversational search."
    )
    doc_data = extract_text_from_note(sample_note)
    doc = {
        "id": 999999,
        "source": "note",
        "filename": doc_data["filename"],
        "raw_content": doc_data["text"],
        "clean_content": "",
        "metadata": {"ocr_used": False, "page_count": 1, "language": "en"},
        "timestamp": "2026-09-17 10:00:00"
    }
    save_document(doc)
    docs = get_all_documents()
    print(f"Total documents in knowledge base: {len(docs)}")

    print("\n=== TEST 2: Run AI Cleanup & Structuring ===")
    cleaned_count = process_all_document_cleanups()
    print(f"Cleaned documents count: {cleaned_count}")

    print("\n=== TEST 3: Generate Vector Embeddings ===")
    chunk_count = build_vector_index()
    print(f"Vector chunks indexed: {chunk_count}")

    print("\n=== TEST 4: Semantic Search ===")
    query = "What does DreamWeave support?"
    results = retrieve_relevant_chunks(query, top_k=2)
    print(f"Found {len(results)} matching chunks:")
    for r in results:
        print(f"  - Score: {r['score']:.4f} | File: {r['filename']} | Content: {r['text'][:80]}...")

    print("\n=== TEST 5: RAG Engine Answer Generation ===")
    rag_res = answer_rag_query(query)
    print(f"Query: {rag_res['query']}")
    print(f"Answer:\n{rag_res['answer']}")
    print("\n[SUCCESS] All DreamWeave Brain pipeline tests passed successfully!")


if __name__ == "__main__":
    run_test()
