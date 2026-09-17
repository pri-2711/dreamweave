import os
import re
import urllib.request
import json
from brain.src.document_store import get_all_documents, update_document


def _heuristic_clean(text: str) -> str:
    """
    Local NLP heuristic cleanup for OCR and raw text:
    - Removes zero-width or non-printable ASCII noise
    - Fixes broken hyphenated words across lines (e.g. 'docu-\nment' -> 'document')
    - Merges awkward single line breaks within paragraphs
    - Normalizes double newlines between paragraphs
    - Cleans up repetitive punctuation and excessive whitespace
    """
    if not text:
        return ""

    # Remove non-printable control characters except linebreaks/tabs
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', text)

    # Reconstruct broken line-end hyphens: e.g. "com-\nplete" -> "complete"
    cleaned = re.sub(r'(\w+)-\s*\n\s*(\w+)', r'\1\2', cleaned)

    # Normalize multiple inline spaces
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)

    # Fix orphan bullet points or numbers followed by extra spaces
    cleaned = re.sub(r'^\s*([•\*\-\d+\.])\s+', r'\1 ', cleaned, flags=re.MULTILINE)

    # Separate blocks by logical paragraphs while joining mid-sentence line breaks
    lines = cleaned.split('\n')
    processed_lines = []
    current_block = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_block:
                processed_lines.append(" ".join(current_block))
                current_block = []
        else:
            # Check if line looks like a header, list item, or structural divider
            is_header_or_list = bool(re.match(r'^([#\*\-•]|\d+[\.\)])', stripped))
            if is_header_or_list and current_block:
                processed_lines.append(" ".join(current_block))
                current_block = [stripped]
            else:
                current_block.append(stripped)

    if current_block:
        processed_lines.append(" ".join(current_block))

    result = "\n\n".join(processed_lines)
    # Final whitespace cleanup
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def _llm_clean(text: str) -> str:
    """
    Optional LLM-assisted cleanup using Gemini or OpenAI API if API key is provided in environment.
    Falls back to heuristic cleaning if API call fails or key is missing.
    """
    gemini_key = os.environ.get("GEMINI_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    prompt = (
        "You are an AI document cleanup & structuring expert for DreamWeave.\n"
        "Clean, fix OCR typos, reconstruct broken paragraphs/menus, format headers, and output clear structured text.\n"
        "Do NOT add conversational commentary. Return ONLY the cleaned document content.\n\n"
        f"Raw Text:\n{text}"
    )

    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}]
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                cleaned_text = res_data['candidates'][0]['content']['parts'][0]['text']
                return cleaned_text.strip()
        except Exception as e:
            print(f"Gemini API cleanup failed ({e}). Falling back to heuristic cleaner.")

    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2
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
                cleaned_text = res_data['choices'][0]['message']['content']
                return cleaned_text.strip()
        except Exception as e:
            print(f"OpenAI API cleanup failed ({e}). Falling back to heuristic cleaner.")

    return _heuristic_clean(text)


def clean_document_content(raw_text: str) -> str:
    """Clean raw text using LLM if available, otherwise heuristic NLP cleaner."""
    if not raw_text or not raw_text.strip():
        return ""
    
    # Try LLM first if env key is available, else heuristic
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY"):
        return _llm_clean(raw_text)
    else:
        return _heuristic_clean(raw_text)


def process_all_document_cleanups():
    """Iterate through all documents in knowledge store and populate clean_content if missing."""
    documents = get_all_documents()
    cleaned_count = 0

    for doc in documents:
        # Clean if clean_content is empty or identical to raw_content
        raw = doc.get("raw_content", "")
        clean = doc.get("clean_content", "")

        if raw and not clean:
            print(f"Cleaning document ID {doc.get('id')} ({doc.get('filename')})...")
            cleaned_text = clean_document_content(raw)
            update_document(doc.get("id"), {"clean_content": cleaned_text})
            cleaned_count += 1

    return cleaned_count
