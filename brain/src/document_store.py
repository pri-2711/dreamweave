import json
import os

KNOWLEDGE_FILE = "brain/data/knowledge.json"


def _ensure_storage_exists():
    os.makedirs(os.path.dirname(KNOWLEDGE_FILE), exist_ok=True)
    if not os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def get_all_documents():
    """Retrieve all ingested documents from the document store."""
    _ensure_storage_exists()
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def save_document(document):
    """Save a single new document into the document store."""
    documents = get_all_documents()
    documents.append(document)
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=4, ensure_ascii=False)


def save_all_documents(documents):
    """Save the full list of documents into the document store."""
    _ensure_storage_exists()
    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=4, ensure_ascii=False)


def get_document_by_id(doc_id):
    """Find a document by its unique ID."""
    documents = get_all_documents()
    for doc in documents:
        if str(doc.get("id")) == str(doc_id):
            return doc
    return None


def update_document(doc_id, updated_fields):
    """Update fields of an existing document by ID."""
    documents = get_all_documents()
    updated = False
    for i, doc in enumerate(documents):
        if str(doc.get("id")) == str(doc_id):
            documents[i].update(updated_fields)
            updated = True
            break
    if updated:
        save_all_documents(documents)
    return updated