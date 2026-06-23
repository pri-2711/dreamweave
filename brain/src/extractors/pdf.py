import fitz
import os
import tempfile

from brain.src.extractors.image import (
    extract_text_from_image
)


def extract_text_from_pdf(pdf_path):

    document = fitz.open(pdf_path)

    page_count = len(document)
    ocr_used = False

    text = ""

    # Try direct extraction first
    for page in document:
        text += page.get_text()
        text += "\n"

    text = text.strip()

    # If text exists, return it
    if text:
        document.close()

        return {
            "text": text,
            "ocr_used": ocr_used,
            "page_count": page_count
        }

    print("\nScanned PDF detected. Running OCR...\n")

    ocr_used = True
    all_text = ""

    # Temporary folder gets deleted automatically
    with tempfile.TemporaryDirectory() as temp_dir:

        for page_num in range(page_count):

            page = document.load_page(page_num)

            # Higher DPI = better OCR
            pix = page.get_pixmap(dpi=300)

            image_path = os.path.join(
                temp_dir,
                f"page_{page_num}.png"
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

    return {
        "text": all_text.strip(),
        "ocr_used": ocr_used,
        "page_count": page_count
    }