from flask import Flask, request, jsonify
from utils.database_utils import create_table_if_not_exists, update_flag, load_ads

app = Flask(__name__)
TABLE_NAME = 'ads'

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

if __name__ == '__main__':
    create_table_if_not_exists(TABLE_NAME)
    app.run(debug=True)