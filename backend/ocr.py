import pytesseract

from PIL import Image
from pdf2image import convert_from_path

from config import (
    TESSERACT_PATH,
    POPPLER_PATH
)

# Configure Tesseract
pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH


def perform_ocr(image: Image.Image) -> str:
    """
    Extract text from a single image.
    """

    text = pytesseract.image_to_string(
        image,
        lang="eng",
        config="--oem 3 --psm 6"
    )

    return text.strip()


def extract_text_from_images(images: list[Image.Image]) -> str:
    """
    Extract text from multiple images.
    """

    extracted_text = []

    for image in images:

        text = perform_ocr(image)

        if text:
            extracted_text.append(text)

    return "\n\n".join(extracted_text)


def convert_pdf_to_images(pdf_path):
    """
    Convert PDF pages into PIL images.
    """

    return convert_from_path(
        pdf_path,
        poppler_path=POPPLER_PATH
    )