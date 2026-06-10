import pytesseract
from PIL import Image

# Change this path only if your installation is elsewhere
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text_from_image(image_path):
    """
    Extract text from image using OCR.
    """

    image = Image.open(image_path)

    text = pytesseract.image_to_string(image)

    return text