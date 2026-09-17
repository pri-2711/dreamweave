from brain.src.extractors.image import extract_text_from_image
from brain.src.extractors.pdf import extract_text_from_pdf
from brain.src.extractors.notes import extract_text_from_note
from brain.src.document_store import save_document, get_all_documents
from brain.src.cleaner import process_all_document_cleanups
from brain.src.vector_store import build_vector_index, load_vector_store
from brain.src.retrieval.retriever import retrieve_relevant_chunks
from brain.src.rag.rag_engine import answer_rag_query

from datetime import datetime
import os


def image_ocr_menu():
    image_path = input("\nEnter image path: ").strip()
    try:
        text = extract_text_from_image(image_path)
        document = {
            "id": int(datetime.now().timestamp()),
            "source": "image",
            "filename": os.path.basename(image_path),
            "raw_content": text,
            "clean_content": "",
            "metadata": {
                "ocr_used": True,
                "page_count": 1,
                "language": "en",
                "ocr_engine": "tesseract"
            },
            "timestamp": str(datetime.now())
        }
        save_document(document)
        print("\n===== EXTRACTED TEXT =====\n")
        print(text)
        print("\nDocument saved successfully!")
    except Exception as e:
        print(f"\nError: {e}")


def pdf_menu():
    pdf_path = input("\nEnter PDF path: ").strip()
    try:
        pdf_data = extract_text_from_pdf(pdf_path)
        text = pdf_data["text"]
        ocr_used = pdf_data["ocr_used"]
        page_count = pdf_data["page_count"]

        document = {
            "id": int(datetime.now().timestamp()),
            "source": "pdf",
            "filename": os.path.basename(pdf_path),
            "raw_content": text,
            "clean_content": "",
            "metadata": {
                "ocr_used": ocr_used,
                "page_count": page_count,
                "language": "en",
                "ocr_engine": "tesseract" if ocr_used else None
            },
            "timestamp": str(datetime.now())
        }
        save_document(document)
        print("\n===== EXTRACTED TEXT =====\n")
        print(text)
        print("\nDocument saved successfully!")
    except Exception as e:
        print(f"\nError: {e}")


def note_menu():
    print("\n--- Note / Text Ingestion ---")
    print("1. Enter text note directly")
    print("2. Import text file (.txt, .md)")
    choice = input("\nEnter choice: ").strip()

    if choice == "1":
        note_text = input("\nEnter your note text:\n").strip()
        filename = "raw_note.txt"
    elif choice == "2":
        file_path = input("\nEnter text file path: ").strip()
        note_data = extract_text_from_note(file_path)
        note_text = note_data["text"]
        filename = note_data["filename"]
    else:
        print("Invalid choice.")
        return

    if not note_text:
        print("Note text cannot be empty.")
        return

    document = {
        "id": int(datetime.now().timestamp()),
        "source": "note",
        "filename": filename,
        "raw_content": note_text,
        "clean_content": "",
        "metadata": {
            "ocr_used": False,
            "page_count": 1,
            "language": "en",
            "ocr_engine": None
        },
        "timestamp": str(datetime.now())
    }
    save_document(document)
    print("\nNote saved successfully!")


def cleanup_menu():
    print("\nRunning AI Cleanup & Structuring on uncleaned documents...")
    count = process_all_document_cleanups()
    if count > 0:
        print(f"\nCompleted AI cleanup on {count} document(s).")
    else:
        print("\nAll documents already cleaned or no raw documents found.")


def embeddings_menu():
    print("\nGenerating Vector Embeddings for knowledge base...")
    count = build_vector_index()
    print(f"\nVector embedding index built. Total indexed chunks: {count}")


def search_menu():
    query = input("\nEnter search query: ").strip()
    if not query:
        return
    print("\nSearching vector database...")
    results = retrieve_relevant_chunks(query, top_k=3)
    if not results:
        print("No matching results found. Make sure vector embeddings are generated.")
        return

    print("\n===== TOP SEARCH RESULTS =====")
    for idx, r in enumerate(results, 1):
        print(f"\n[{idx}] File: {r.get('filename')} | Doc ID: {r.get('doc_id')} | Score: {r.get('score'):.4f}")
        print(f"Content:\n{r.get('text')}")


def rag_chat_menu():
    print("\n===== DREAMWEAVE RAG CHAT =====")
    print("Type your question to search & ask the knowledge base (or 'back' to return).\n")
    while True:
        query = input("\nUser Query > ").strip()
        if query.lower() in ["back", "exit", "quit"]:
            break
        if not query:
            continue

        result = answer_rag_query(query)
        print("\n===== RESPONSE =====")
        print(result["answer"])
        if result.get("sources"):
            print("\nSources:")
            for s in result["sources"]:
                print(f" - {s.get('filename')} (Score: {s.get('score'):.2f})")


def view_documents_menu():
    docs = get_all_documents()
    print(f"\n===== KNOWLEDGE BASE DOCUMENTS ({len(docs)}) =====")
    if not docs:
        print("No documents stored yet.")
        return

    for doc in docs:
        clean_status = "Cleaned" if doc.get("clean_content") else "Raw Only"
        print(f"ID: {doc.get('id')} | Source: {doc.get('source')} | File: {doc.get('filename')} | Status: {clean_status}")


def main():
    while True:
        print("\n===== DREAMWEAVE BRAIN 🧠✨ =====")
        print("1. Extract text from Image")
        print("2. Extract text from PDF")
        print("3. Add Raw Text Note / File")
        print("4. Perform AI Cleanup & Structuring")
        print("5. Generate Vector Embeddings")
        print("6. Perform Semantic Search")
        print("7. Interactive RAG Chatbot")
        print("8. View Knowledge Base Documents")
        print("9. Exit")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            image_ocr_menu()
        elif choice == "2":
            pdf_menu()
        elif choice == "3":
            note_menu()
        elif choice == "4":
            cleanup_menu()
        elif choice == "5":
            embeddings_menu()
        elif choice == "6":
            search_menu()
        elif choice == "7":
            rag_chat_menu()
        elif choice == "8":
            view_documents_menu()
        elif choice == "9":
            print("\nGoodbye!")
            break
        else:
            print("\nInvalid choice. Please select 1-9.")


if __name__ == "__main__":
    main()