import fitz  # PyMuPDF
import pytesseract
import cv2
import os
import json
import re
from PIL import Image
import numpy as np
from tqdm import tqdm

PDF_PATH = "vAlmIkirAmAyaNa.pdf"
TEMP_DIR = "ramayana_pages"
OUTPUT_JSON = "ramayana_slokas.json"
LANG = "san"

def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def pdf_to_images(pdf_path):
    ensure_dir(TEMP_DIR)
    img_paths = sorted([
        os.path.join(TEMP_DIR, f) for f in os.listdir(TEMP_DIR)
        if f.lower().endswith(('.png', '.jpg', '.jpeg'))
    ])
    return img_paths[58:]  # Start from page 59 (index 58)

def preprocess_image(image_path):
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(thresh)

def clean_text_block(text):
    lines = text.split("\n")
    devanagari_lines = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if sum(0x0900 <= ord(ch) <= 0x097F for ch in line) > len(line) * 0.3:
            devanagari_lines.append(line)
    return "\n".join(devanagari_lines)

def extract_slokas_from_text(text):
    """
    Extract slokas from text.
    Note: Kanda and Sarga are currently hardcoded to 1 and should be dynamically detected later if required.
    """
    # Sloka structure: ... ॥ X ॥ (Sanskrit punctuation)
    blocks = re.split(r"॥\s*(\d+)\s*॥", text)
    slokas = []
    kanda = 1
    sarga = 1
    for i in tqdm(range(1, len(blocks), 2), desc="Extracting slokas"):
        sloka_number = int(blocks[i])
        body = blocks[i - 1].strip().replace("\n", " ")
        slokas.append({
            "kanda": kanda,
            "sarga": sarga,
            "sloka": sloka_number,
            "text": body + f" ॥ {sloka_number} ॥"
        })
    return slokas

def run_ocr_pipeline():
    # Processing from page 59 to end (images already extracted)
    img_paths = pdf_to_images(PDF_PATH)
    all_slokas = []

    for img_path in tqdm(img_paths, desc="Processing pages"):
        image = preprocess_image(img_path)
        ocr_text = pytesseract.image_to_string(image, lang=LANG)
        ocr_text = clean_text_block(ocr_text)
        slokas = extract_slokas_from_text(ocr_text)
        all_slokas.extend(slokas)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump({"slokas": all_slokas}, f, ensure_ascii=False, indent=2)
    print(f"✅ Done. Extracted {len(all_slokas)} slokas to {OUTPUT_JSON}")

if __name__ == "__main__":
    run_ocr_pipeline()