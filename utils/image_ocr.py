import easyocr
import re
import os
import cv2
import numpy as np


def preprocess_image(path):
    img = cv2.imread(path)

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply bilateral filter to reduce noise but keep edges sharp
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)

    # Use adaptive thresholding
    thresh = cv2.adaptiveThreshold(
        filtered, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
    )

    return thresh


def clean_and_match_plates(ocr_texts):
    plate_candidates = set()
    for raw in ocr_texts:
        text = raw.strip().upper()

        # Skip short or clearly non-plate strings
        if len(text) < 5:
            continue

        # Fix common OCR misreads in plate-like strings (length ~7)
        if len(text) in [6, 7, 8]:
            chars = list(text)
            if len(chars) > 2:
                # Only apply substitutions to specific positions
                if chars[2] == 'O':
                    chars[2] = '0'
                elif chars[2] == 'I' or chars[2] == 'L':
                    chars[2] = '1'
            text = ''.join(chars)

        # Match UK plate pattern
        matches = re.findall(r"\b[A-Z]{2}[\dIOL]{2}\s?[A-Z]{3}\b", text)
        plate_candidates.update(matches)

    return plate_candidates

# Find reg plate from single image


def ocr_reg_plate_single(ad_id, image_index):
    reader = easyocr.Reader(['en'], gpu=True)
    img_path = f'images/{ad_id}/{str(image_index).zfill(2)}.jpg'
    try:
        # preprocessed_img = preprocess_image(img_path)
        results = reader.readtext(img_path, detail=0, paragraph=False)

        print(f"All texts found: {results}")
        plate_set = clean_and_match_plates(results)
        print(f"Possible plates: {plate_set}")
        return list(plate_set)
    except Exception as e:
        print(f'❌ OCR failed on {img_path}: {e}')
        return []
