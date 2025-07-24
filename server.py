from flask import Flask, request, jsonify, send_from_directory
from utils.database_utils import create_table_if_not_exists, update_flag, load_ads
from utils.mot_history import get_mot_history


app = Flask(__name__)
TABLE_NAME = 'ads'
THUMBNAIL_DIR = 'thumbnails'

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
    return jsonify(ads)

@app.route('/api/thumbnail/<ad_id>', methods = ['GET'])
def serve_thumbnail(ad_id):
    filename = f'{ad_id}.jpg'
    return send_from_directory(THUMBNAIL_DIR, filename)

@app.route('/api/mot_history', methods = ['GET'])
def query_mot_history():
    try:
        reg = request.args.get("reg")
        if not reg:
            return jsonify({'error': 'Missing registration number'}), 400
        
        result = get_mot_history(reg.upper())
        
        if 'error' in result:
            return jsonify(result), 403 if 'Forbidden' in result.get('details', '') else 500
        
        return jsonify(result)
    except Exception as e:
        print('❌ Internal server error in /api/mot_history:', str(e))
        

if __name__ == '__main__':
    create_table_if_not_exists(TABLE_NAME)
    app.run(debug=True)