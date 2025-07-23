import easyocr, re, os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = 3 # Silence Tensorflow warnings: 0 = all logs, 1 = filter INFO, 2 = filter WARNING, 3 = filter ERROR

# Move to new 'image_ocr.py'?
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
        matches = re.findall(r"\b[A-Z]{2}\d{2}\s?[A-Z]{3}\b", text)
        plate_candidates.update(matches)

    return plate_candidates

# Read registration plates from images
def ocr_reg_plate(ad_id):
    folder = f'images/{ad_id}'
    reader = easyocr.Reader(['en'], gpu = True)
    
    all_texts = []
        
    for filename in os.listdir(folder):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            img_path = os.path.join(folder, filename)
            try:
                results = reader.readtext(img_path, detail = 0, paragraph = False)
                all_texts.extend(results)

            except Exception as e:
                print(f"Failed to process {filename}: {e}")
                
    plate_set = clean_and_match_plates(all_texts)
                    
    print(f"Possible plates for {ad_id}: {plate_set}")    
    return plate_set