import json
import os

KNOWLEDGE_FILE = "brain/data/knowledge.json"


def save_document(document):

    if not os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, "w") as f:
            json.dump([], f)

    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        documents = json.load(f)

    documents.append(document)

    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as f:
        json.dump(
            documents,
            f,
            indent=4,
            ensure_ascii=False
        )