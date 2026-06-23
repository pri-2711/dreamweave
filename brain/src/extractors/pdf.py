import fitz
import os

from brain.src.extractors.image import (
    extract_text_from_image
)


def extract_text_from_pdf(pdf_path):

    document = fitz.open(pdf_path)

    text = ""

    # Try direct extraction first
    for page in document:
        text += page.get_text()
        text += "\n"

    text = text.strip()

    # If text exists, return it
    if text:
        document.close()
        return text

    print("\nScanned PDF detected. Running OCR...\n")

    # Create temp folder if needed
    os.makedirs("temp", exist_ok=True)

    all_text = ""

    # Convert pages to images and OCR them
    for page_num in range(len(document)):

        page = document.load_page(page_num)

        pix = page.get_pixmap(dpi=300)

        image_path = (
            f"temp/page_{page_num}.png"
        )

        pix.save(image_path)

        page_text = (
            extract_text_from_image(
                image_path
            )
        )

        all_text += page_text
        all_text += "\n"

    document.close()

    return all_text.strip()