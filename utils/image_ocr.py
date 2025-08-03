import easyocr
import re
import os
import cv2
import numpy as np


def crop_likely_plate_region(img):
    h, w = img.shape[:2]
    return img[h//2:h, :]  # Bottom half only


def preprocess_image(path, debug_path=None):
    img = cv2.imread(path)

    # Resize (some images may be too large or too small)
    # img = cv2.resize(img, (800, int(img.shape[0] * 800 / img.shape[1])))

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Crop to where license plate is likely to be (bottom half)
    gray = crop_likely_plate_region(gray)

    # CLAHE contrast enhancement
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)

    # Apply bilateral filter (denoise)
    filtered = cv2.bilateralFilter(enhanced, 11, 17, 17)

    # Thresholding
    _, thresh = cv2.threshold(
        filtered, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Save preprocessed image for debugging
    if debug_path:
        os.makedirs(os.path.dirname(debug_path), exist_ok=True)
        cv2.imwrite(debug_path, thresh)

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
    debug_path = f'debug/{ad_id}_{str(image_index).zfill(2)}_preprocessed.jpg'
    try:
        preprocessed_img = preprocess_image(img_path, debug_path)

        results = reader.readtext(preprocessed_img, detail=0, paragraph=False)

        print(f"All texts found: {results}")
        plate_set = clean_and_match_plates(results)
        print(f"Possible plates: {plate_set}")
        return list(plate_set)
    except Exception as e:
        print(f'❌ OCR failed on {img_path}: {e}')
        return []
