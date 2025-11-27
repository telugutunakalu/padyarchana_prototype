"""
OCR Service for extracting Telugu text from images using Tesseract.

Requirements:
- tesseract-ocr: sudo apt-get install tesseract-ocr
- tesseract-ocr-tel: sudo apt-get install tesseract-ocr-tel
- pytesseract: pip install pytesseract
- Pillow: pip install Pillow
"""
import os
from pathlib import Path
from typing import Tuple, Optional

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False


def check_tesseract_available() -> Tuple[bool, str]:
    """
    Check if Tesseract OCR is available and Telugu language pack is installed.

    Returns:
        Tuple of (is_available, message)
    """
    if not TESSERACT_AVAILABLE:
        return False, "pytesseract or Pillow not installed. Run: pip install pytesseract Pillow"

    try:
        # Check if tesseract is installed
        version = pytesseract.get_tesseract_version()

        # Check if Telugu language pack is available
        languages = pytesseract.get_languages()
        if 'tel' not in languages:
            return False, f"Telugu language pack not found. Available: {languages}. Run: sudo apt-get install tesseract-ocr-tel"

        return True, f"Tesseract {version} with Telugu support available"
    except Exception as e:
        return False, f"Tesseract not available: {str(e)}. Run: sudo apt-get install tesseract-ocr tesseract-ocr-tel"


def extract_telugu_text(image_path: str) -> Tuple[str, Optional[str]]:
    """
    Extract Telugu text from an image using Tesseract OCR.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (extracted_text, error_message)
        If successful, error_message is None
        If failed, extracted_text is empty and error_message contains the error
    """
    if not TESSERACT_AVAILABLE:
        return "", "OCR libraries not installed. Run: pip install pytesseract Pillow"

    if not os.path.exists(image_path):
        return "", f"Image file not found: {image_path}"

    try:
        # Open and process image
        image = Image.open(image_path)

        # Convert to RGB if necessary (handles PNG with transparency)
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        # Extract text using Telugu language
        # psm 6: Assume a single uniform block of text
        custom_config = r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(
            image,
            lang='tel',
            config=custom_config
        )

        # Clean up the extracted text
        text = text.strip()

        return text, None

    except Exception as e:
        return "", f"OCR Error: {str(e)}"


def extract_text_with_confidence(image_path: str) -> Tuple[str, float, Optional[str]]:
    """
    Extract Telugu text from an image with confidence score.

    Args:
        image_path: Path to the image file

    Returns:
        Tuple of (extracted_text, confidence_score, error_message)
    """
    if not TESSERACT_AVAILABLE:
        return "", 0.0, "OCR libraries not installed"

    if not os.path.exists(image_path):
        return "", 0.0, f"Image file not found: {image_path}"

    try:
        image = Image.open(image_path)

        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        # Get detailed OCR data including confidence
        data = pytesseract.image_to_data(
            image,
            lang='tel',
            output_type=pytesseract.Output.DICT
        )

        # Calculate average confidence for non-empty text
        confidences = [
            conf for conf, text in zip(data['conf'], data['text'])
            if text.strip() and conf != -1
        ]

        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Get the text
        text = pytesseract.image_to_string(image, lang='tel').strip()

        return text, avg_confidence, None

    except Exception as e:
        return "", 0.0, f"OCR Error: {str(e)}"


def preprocess_image_for_ocr(image_path: str):
    """
    Preprocess image to improve OCR accuracy.

    Args:
        image_path: Path to the image file

    Returns:
        Preprocessed PIL Image or None if failed
    """
    if not TESSERACT_AVAILABLE:
        return None

    try:
        image = Image.open(image_path)

        # Convert to RGB
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        # Convert to grayscale for better OCR
        image = image.convert('L')

        # Increase contrast (simple thresholding)
        # This can help with scanned documents
        threshold = 128
        image = image.point(lambda p: 255 if p > threshold else 0)

        return image

    except Exception as e:
        print(f"Image preprocessing error: {e}")
        return None
