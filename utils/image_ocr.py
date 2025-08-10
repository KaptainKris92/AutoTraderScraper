import easyocr
import re
import string
import os
import cv2
import numpy as np
from ultralytics import YOLO  # For detecting reg plate in image

# Storage roots (env-aware; local -> ./data, Railway -> /data)
DATA_DIR = os.getenv("DATA_DIR", "./data")
IMAGES_DIR = os.getenv("UPLOAD_DIR", os.path.join(DATA_DIR, "images"))
DEBUG_DIR = os.getenv("DEBUG_DIR", os.path.join(DATA_DIR, "debug"))

# Ensure folders exist in dev (Railway volume exists at runtime)
os.makedirs(IMAGES_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True)

# Initialize the OCR reader
reader = easyocr.Reader(['en'], gpu=False)

# Load pretrained license plate detector
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_MODEL_PATH = os.path.join(_THIS_DIR, "..", "models",
                           "license_plate_detector.pt")
_MODEL_PATH = os.path.normpath(_MODEL_PATH)

reg_plate_model = YOLO(_MODEL_PATH).to("cpu")

# Mapping dictionaries for character conversion
dict_char_to_int = {'O': '0',
                    'I': '1',
                    'J': '3',
                    'A': '4',
                    'G': '6',
                    'S': '5'}

dict_int_to_char = {'0': 'O',
                    '1': 'I',
                    '3': 'J',
                    '4': 'A',
                    '6': 'G',
                    '5': 'S'}


def crop_likely_plate_region(img):
    h, w = img.shape[:2]
    return img[h//3:, :]  # Bottom 2/3 only


def detect_plate_and_crop(img, debug_img=True):
    results = reg_plate_model.predict(source=img, conf=0.5)
    if len(results[0].boxes) == 0:
        return None

    # Assume first box is the plate
    box = results[0].boxes[0].xyxy[0].cpu().numpy().astype(int)
    x1, y1, x2, y2 = box
    cropped_image = img[y1:y2, x1:x2]
    return cropped_image, (x1, y1, x2, y2)


def preprocess_image(path, debug_path=None):
    path = str(path)  # Make sure path is a string for OpenCV
    img = cv2.imread(path)  # BGR

    # ⚠️ do NOT preprocess before YOLO
    cropped, plate_bbox = detect_plate_and_crop(img)

    if cropped is None:
        print("No plate detected. Falling back to bottom 2/3 crop.")
        cropped = crop_likely_plate_region(img)
        plate_bbox = None

    # Grayscale and denoise *after* cropping
    gray = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
    filtered = cv2.bilateralFilter(gray, 11, 17, 17)

    if debug_path:
        os.makedirs(os.path.dirname(debug_path), exist_ok=True)
        cv2.imwrite(debug_path, filtered)

    return filtered


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

# Code borrowed from https://github.com/arij01/PlatePatrol/


def license_complies_format(text):

    if len(text) != 7:
        return False

    if (text[0] in string.ascii_uppercase or text[0] in dict_int_to_char.keys()) and \
       (text[1] in string.ascii_uppercase or text[1] in dict_int_to_char.keys()) and \
       (text[2] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[2] in dict_char_to_int.keys()) and \
       (text[3] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9'] or text[3] in dict_char_to_int.keys()) and \
       (text[4] in string.ascii_uppercase or text[4] in dict_int_to_char.keys()) and \
       (text[5] in string.ascii_uppercase or text[5] in dict_int_to_char.keys()) and \
       (text[6] in string.ascii_uppercase or text[6] in dict_int_to_char.keys()):
        return True
    else:
        return False


def format_license(text):

    license_plate_ = ''
    mapping = {0: dict_int_to_char, 1: dict_int_to_char, 4: dict_int_to_char, 5: dict_int_to_char, 6: dict_int_to_char,
               2: dict_char_to_int, 3: dict_char_to_int}
    for j in [0, 1, 2, 3, 4, 5, 6]:
        if text[j] in mapping[j].keys():
            license_plate_ += mapping[j][text[j]]
        else:
            license_plate_ += text[j]

    return license_plate_


def read_license_plate(license_plate_crop):

    detections = reader.readtext(license_plate_crop)

    for detection in detections:
        bbox, text, score = detection

        text = text.upper().replace(' ', '')

        if license_complies_format(text):
            return format_license(text), score

    return None, None

#####################

# Find reg plate from single image


def ocr_reg_plate_single(ad_id, image_index):
    img_path = os.path.join(
        IMAGES_DIR, ad_id, f"{str(image_index).zfill(2)}.jpg")
    debug_path = os.path.join(
        DEBUG_DIR, f"{ad_id}_{str(image_index).zfill(2)}_preprocessed.jpg")
    try:
        preprocessed_img = preprocess_image(img_path, debug_path)

        # Use PlatePatrol logic for OCR + validation
        license_plate_text, text_score = read_license_plate(preprocessed_img)

        if license_plate_text:
            print(
                f"✅ Detected license plate: {license_plate_text} (score: {text_score:.2f})")
            return [license_plate_text]
        else:
            print("❌ No valid license plate detected.")
            return []

    except Exception as e:
        print(f'❌ OCR failed on {img_path}: {e}')
        return []


if __name__ == "__main__":
    ocr_reg_plate_single('202507154490830', '09')
