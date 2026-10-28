"""
RAG Prompt Builder for DreamWeave.
Formats grounded context prompts distinguishing user Space knowledge from general model knowledge.
"""

from typing import List, Dict, Any, Optional


def build_grounded_rag_prompt(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    space_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Build a grounded RAG prompt and system instruction for Gemini API.
    """
    space_ctx = f"Space: '{space_name}'" if space_name else "Current Space"

    system_instruction = (
        "You are DreamWeave Assistant, an intelligent workspace assistant.\n"
        f"You are currently assisting the user in {space_ctx}.\n"
        "Your priority is to provide accurate, grounded answers using the user's saved Space Knowledge provided below.\n"
        "Rules:\n"
        "1. If the retrieved context contains relevant information, use it to form a helpful, detailed answer.\n"
        "2. Cite your sources clearly using the content references (e.g. [Source: content_id]).\n"
        "3. If the retrieved context is empty or does not fully cover the question, answer helpfully using general knowledge while explicitly indicating that parts of the answer are based on general AI knowledge rather than saved Space items.\n"
        "4. Never invent or falsify saved documents that do not exist in the context."
    )

    context_text = ""
    if retrieved_chunks:
        context_text = "=== RETRIEVED SPACE KNOWLEDGE ===\n"
        for idx, chunk in enumerate(retrieved_chunks, 1):
            cid = chunk.get("content_id", "unknown")
            score = chunk.get("score", 0.0)
            context_text += f"[Excerpt {idx} | Content Reference: {cid} | Score: {score:.2f}]\n"
            context_text += f"{chunk.get('text', '').strip()}\n\n"
    else:
        context_text = "=== RETRIEVED SPACE KNOWLEDGE ===\n[No relevant saved documents found in this Space for the query]\n\n"

    user_prompt = (
        f"{context_text}"
        f"=== USER QUESTION ===\n{question}\n"
    )

    return {
        "system_instruction": system_instruction,
        "prompt": user_prompt
    }


def build_conversation_rag_prompt(
    messages: List[Dict[str, Any]],
    new_message: str,
    retrieved_chunks: List[Dict[str, Any]],
    space_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Build a conversational grounded RAG prompt preserving chat history.
    """
    space_ctx = f"Space: '{space_name}'" if space_name else "Current Space"

    system_instruction = (
        "You are DreamWeave Assistant, an intelligent workspace chat assistant.\n"
        f"You are conversing with the user inside {space_ctx}.\n"
        "Ground your answers in the user's saved Space Knowledge provided below whenever relevant.\n"
        "Cite source documents using [Source: content_id] when referencing specific content.\n"
        "Maintain a helpful, friendly, and concise conversational tone."
    )

    context_text = ""
    if retrieved_chunks:
        context_text = "=== RETRIEVED SPACE KNOWLEDGE ===\n"
        for idx, chunk in enumerate(retrieved_chunks, 1):
            cid = chunk.get("content_id", "unknown")
            score = chunk.get("score", 0.0)
            context_text += f"[Excerpt {idx} | Content Reference: {cid} | Score: {score:.2f}]\n"
            context_text += f"{chunk.get('text', '').strip()}\n\n"
    else:
        context_text = "=== RETRIEVED SPACE KNOWLEDGE ===\n[No specific saved documents matched the latest query]\n\n"

    history_text = "=== CONVERSATION HISTORY ===\n"
    for msg in messages[-6:]:  # Last 6 messages for context
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "").strip()
        history_text += f"{role}: {content}\n"

    user_prompt = (
        f"{context_text}"
        f"{history_text}\n"
        f"User: {new_message}\n"
        f"Assistant:"
    )

    return {
        "system_instruction": system_instruction,
        "prompt": user_prompt
    }


def build_content_generation_prompt(
    prompt: str,
    generation_type: str,
    retrieved_chunks: List[Dict[str, Any]],
    space_name: Optional[str] = None
) -> Dict[str, str]:
    """
    Build prompt for generating structured AI content (itinerary, summary, suggestion, checklist).
    """
    space_ctx = f"Space: '{space_name}'" if space_name else "Current Space"

    system_instruction = (
        "You are DreamWeave AI Creator, a specialized creative generator for personal and collaborative workspaces.\n"
        f"You are generating a structured '{generation_type}' item inside {space_ctx}.\n"
        "Use the user's Space knowledge when available to make the content rich, contextual, and accurate.\n"
        "Format the output clearly using Markdown headers, bullet points, or structured sections."
    )

    context_text = ""
    if retrieved_chunks:
        context_text = "=== RELEVANT SPACE KNOWLEDGE ===\n"
        for idx, chunk in enumerate(retrieved_chunks, 1):
            cid = chunk.get("content_id", "unknown")
            context_text += f"[Item {idx} | Ref: {cid}]\n{chunk.get('text', '').strip()}\n\n"

    user_prompt = (
        f"{context_text}"
        f"=== INSTRUCTIONS ===\n"
        f"Generate a high-quality {generation_type} based on the following request:\n"
        f"{prompt}\n"
    )

    return {
        "system_instruction": system_instruction,
        "prompt": user_prompt
    }

