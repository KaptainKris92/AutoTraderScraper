from flask import Flask, request, jsonify, send_from_directory
from utils.database_utils import create_ads_table, update_flag, load_ads, save_mot_history, get_mot_histories, delete_mot_history, bind_mot_to_ad
from utils.mot_history import get_mot_history
from pathlib import Path
from scraper import download_pictures

app = Flask(__name__)
TABLE_NAME = 'ads'
THUMBNAIL_DIR = Path('thumbnails')

import re

def extract_highest_res_images(ad_urls):
    pattern = re.compile(r"/w(\d+)/([a-f0-9]+)\.jpg")
    best_images = {}

    for url in ad_urls:
        match = pattern.search(url)
        if match:
            width = int(match.group(1))
            key = match.group(2)  # hash name of image
            if key not in best_images or width > best_images[key][0]:
                best_images[key] = (width, url)

    return [info[1] for info in best_images.values()]


@app.route('/api/fav_exc', methods = ['POST'])
def favourite_or_exclude_ad():
    data = request.get_json()
    ad_id = data.get('ad_id')
    operation = data.get('operation')    
    value = data.get('value')
    if value is None:
        return jsonify({'error': 'Missing value. Value must be 0 or 1.'}), 400
    elif value not in [0, 1]:
        return jsonify({'error': 'Invalid value. Value must be 0 or 1.'}), 400
    else:
        value = int(value)
    
    if not ad_id:
        return jsonify({'error': 'Missing ad_id'}), 400    
    if not operation:
        return jsonify({'error': 'Missing operation'}), 400
    
    if operation == 'favourite':
        column = 'Favourited'
    elif operation == 'exclude':
        column = 'Excluded'
    else:
        return jsonify({'error': f"Invalid operation '{operation}'. Must be either 'favourite' or 'exclude'"}), 400
    
    update_flag(ad_id, column, value, TABLE_NAME)
    return jsonify({"status": "ok", "ad_id": ad_id, column: value})

@app.route('/api/ads', methods = ['GET'])
def get_ads():
    ads = load_ads('ads')
    
    if not ads:
        return jsonify({"message": "No ads found", "data": []}), 200
    return jsonify(ads)

@app.route('/api/thumbnail/<ad_id>', methods = ['GET'])
def serve_thumbnail(ad_id):
    filename = f'{ad_id}.jpg'
    return send_from_directory(THUMBNAIL_DIR, filename)

@app.route('/api/gallery-image/<ad_id>/<image_index>', methods=['GET', 'HEAD'])
def serve_gallery_image(ad_id, image_index):
    filename = f"{str(image_index).zfill(2)}.jpg"
    folder = Path("images") / ad_id
    return send_from_directory(folder, filename)

# Get new MOT History through API
@app.route('/api/mot_history/query', methods = ['GET'])
def query_mot_history():
    try:
        reg = request.args.get("reg").replace(" ", "").strip()
        if not reg:
            return jsonify({'error': 'Missing registration number'}), 400
        
        result = get_mot_history(reg.upper())
        
        if 'error' in result:
            return jsonify(result), 403 if 'Forbidden' in result.get('details', '') else 500
        
        return jsonify(result)
    except Exception as e:
        print('❌ Internal server error in /api/mot_history:', str(e))
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500
    
@app.route('/api/mot_history', methods = ['POST'])
def save_mot_entry():
    data = request.get_json()
    reg = data.get('registration')
    mot_data = data.get('data')
    ad_id = data.get('ad_id')
    if not reg or not mot_data:
        return jsonify({'error': 'Missing registration or MOT data'}), 400
    save_mot_history(reg, mot_data, ad_id)
    return jsonify({'status': 'saved'})

# Get MOT History from local database
@app.route('/api/mot_history', methods = ['GET'])
def get_all_mot():
    ad_id = request.args.get('ad_id')
    if ad_id == "" or ad_id is None:
        ad_id = None
        print('Fetching all MOT histories')
    else:
        print(f'Fetching MOT history for ad_id {ad_id}')
    
    histories = get_mot_histories(ad_id)
    return jsonify(histories)

@app.route('/api/mot_history/bind', methods = ['POST'])
def bind_mot_entry():
    data = request.get_json()
    reg = data.get('registration')
    ad_id = data.get('ad_id')        
    
    if not reg:
        return jsonify({'error': 'Missing registration or Ad ID'}), 400
    
    # Interpret empty string as NULL
    if ad_id == "":
        ad_id = None
        
    bind_mot_to_ad(reg, ad_id)
    return jsonify({'status': 'bound'})

@app.route('/api/mot_history/<reg>', methods = ['DELETE'])
def delete_mot_entry(reg):
    delete_mot_history(reg)
    return jsonify({'status': 'deleted'})

@app.route('/api/download-pictures', methods = ['POST'])
def api_download_pictures():
    data = request.get_json()
    ad_id = data.get('ad_id')
    ad_url = data.get('ad_url')
    
    if isinstance(ad_id, list):
        ad_id = ad_id[0]
    if isinstance(ad_url, list):
        ad_url = ad_url[0]
        
    try:
        download_pictures(ad_id, ad_url)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
@app.route('/api/image-count/<ad_id>')
def image_count(ad_id):
    folder = Path("images") / ad_id
    if not folder.exists():
        return jsonify({"count": 0})
    count = len(list(folder.glob("*.jpg")))
    return jsonify({"count": count})

if __name__ == '__main__':
    create_ads_table(TABLE_NAME)
    app.run(debug=True)