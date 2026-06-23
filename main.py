from brain.src.extractors.image import extract_text_from_image
from brain.src.document_store import save_document
from brain.src.extractors.pdf import extract_text_from_pdf
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

    pdf_path = input(
        "\nEnter PDF path: "
    ).strip()

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

        print(
            "\n===== EXTRACTED TEXT =====\n"
        )
        print(text)

        print(
            "\nDocument saved successfully!"
        )

    except Exception as e:
        print(
            f"\nError: {e}"
        )

def main():
    while True:

        print("\n===== DREAMWEAVE BRAIN =====")
        print("1. Extract text from image")
        print("2. Extract text from PDF")
        print("3. Exit")

        choice = input("\nEnter choice: ").strip()

        if choice == "1":
            image_ocr_menu()

        elif choice == "2":
            pdf_menu()

        elif choice == "3":
            print("\nGoodbye!")
            break

        else:
            print("\nInvalid choice.")


if __name__ == "__main__":
    main()