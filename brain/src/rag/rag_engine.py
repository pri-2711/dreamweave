import os
import json
import urllib.request
from typing import Dict, Any, List
from brain.src.retrieval.retriever import retrieve_relevant_chunks


def _format_context_prompt(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Build grounded context prompt for LLM or synthesis engine."""
    context_str = ""
    for idx, c in enumerate(retrieved_chunks, 1):
        context_str += f"[Source {idx}: Document '{c.get('filename')}' (ID: {c.get('doc_id')}) - Score: {c.get('score'):.2f}]\n"
        context_str += f"{c.get('text')}\n\n"

    prompt = (
        "You are DreamWeave Assistant, an intelligent RAG system.\n"
        "Answer the user query strictly and accurately based ONLY on the retrieved document context below.\n"
        "If the context does not contain enough information to answer the question, clearly state that the answer is not available in the uploaded documents.\n"
        "Include source citations (e.g. [Document: test.pdf]) where appropriate.\n\n"
        f"=== RETRIEVED CONTEXT ===\n{context_str}\n"
        f"=== USER QUERY ===\n{query}\n"
    )
    return prompt


def _synthesize_local_rag_answer(query: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Local fallback grounded RAG answer synthesizer when no external LLM API key is present."""
    if not retrieved_chunks:
        return (
            "[Notice] No relevant information found in the knowledge base for your query.\n"
            "Tip: Make sure you have uploaded documents/notes and generated vector embeddings."
        )

    response = "=== DreamWeave RAG Answer (Grounded Retrieval) ===\n\n"
    response += "Based on your uploaded documents:\n\n"

    for idx, c in enumerate(retrieved_chunks, 1):
        response += f"[Excerpt {idx}] (From '{c.get('filename')}' | Match Score: {c.get('score')*100:.1f}%):\n"
        response += f"> \"{c.get('text').strip()}\"\n\n"

    response += "---"
    return response



def answer_rag_query(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Perform full RAG pipeline:
    1. Retrieve relevant chunks from vector store.
    2. Build context prompt.
    3. Generate response using LLM API if available, or local grounded synthesis engine.
    """
    retrieved_chunks = retrieve_relevant_chunks(query, top_k=top_k)

    if not retrieved_chunks:
        return {
            "query": query,
            "answer": "No relevant documents or chunks found matching your query.",
            "sources": []
        }

    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    prompt = _format_context_prompt(query, retrieved_chunks)
    answer_text = ""

    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                answer_text = res_data['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            print(f"Gemini API request failed ({e}). Using local synthesis fallback.")

    if not answer_text and openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {openai_key}'
                }
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                answer_text = res_data['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"OpenAI API request failed ({e}). Using local synthesis fallback.")

    if not answer_text:
        answer_text = _synthesize_local_rag_answer(query, retrieved_chunks)

    sources = [
        {"filename": c.get("filename"), "doc_id": c.get("doc_id"), "score": c.get("score")}
        for c in retrieved_chunks
    ]

    return {
        "query": query,
        "answer": answer_text,
        "sources": sources,
        "chunks": retrieved_chunks
    }
