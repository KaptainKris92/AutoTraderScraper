from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import utils.database_utils as db
from utils.mot_history import get_mot_history
from utils.scrape_utils import download_pictures, check_caz, scrape_autotrader
from utils.search_utils import generate_autotrader_url
from pathlib import Path
from utils.image_ocr import ocr_reg_plate_single
import threading
import time
import os
from functools import wraps

app = Flask(__name__)
# config.py contains DATA_DIR, UPLOAD_DIR, THUMBNAIL_DIR, etc.
app.config.from_object("config")

# --- CORS ---------------------------------------------------------
# In prod, set ALLOWED_ORIGIN to Netlify URL (e.g., https://autoscraper.netlify.app)
if app.config.get("ALLOWED_ORIGIN"):
    CORS(app, resources={r"/api/*": {"origins": app.config["ALLOWED_ORIGIN"]}})
else:
    CORS(app)  # dev

# --- Optional Basic Auth (protect API so only you can hit it) -----
BASIC_USER = os.getenv("BASIC_AUTH_USERNAME")
BASIC_PASS = os.getenv("BASIC_AUTH_PASSWORD")


def _need_auth():
    return Response("Auth required", 401, {"WWW-Authenticate": 'Basic realm="Private"'})


def _check_auth(auth):
    return auth and auth.username == BASIC_USER and auth.password == BASIC_PASS


def require_basic_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        # if creds not set, no auth in dev
        if not BASIC_USER and not BASIC_PASS:
            return fn(*args, **kwargs)
        auth = request.authorization
        if not _check_auth(auth):
            return _need_auth()
        return fn(*args, **kwargs)
    return wrapper

# Enforce auth for all /api/* routes


@app.before_request
def _lock_down():
    # allow public health without auth
    if request.path == "/api/health":
        return None
    if request.path.startswith("/api/"):
        if not BASIC_USER and not BASIC_PASS:
            return None
        auth = request.authorization
        if not _check_auth(auth):
            return _need_auth()
    return None


# --- Paths / Directories ------------------------------------------
# Use config-provided directories pointed at /data/... on Railway
DATA_DIR = Path(app.config.get("DATA_DIR", "./data"))
IMAGES_ROOT = Path(app.config.get("UPLOAD_DIR", DATA_DIR / "images"))
THUMBNAIL_DIR = Path(app.config.get("THUMBNAIL_DIR", DATA_DIR / "thumbnails"))

# Make sure folders exist (first boot on a fresh volume)
IMAGES_ROOT.mkdir(parents=True, exist_ok=True)
THUMBNAIL_DIR.mkdir(parents=True, exist_ok=True)

TABLE_NAME = 'ads'
db.ensure_tables_exist()

# In-memory progress trackers
# Ad downloads
scrape_progress = {}       # {profile_id: {"status": str}}
scrape_threads = {}        # {profile_id: threading.Thread}
scrape_abort_flags = {}    # {profile_id: threading.Event}
# Picture download
download_status = {}       # {ad_id: {...}}


# %% GET
# -------

#### HEALTH ####

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"ok": True})

# For debugging Railway pandas/numpy import errors


@app.route("/api/diag/python", methods=["GET"])
def diag_python():
    # Don’t import pandas here!
    import sys
    import os
    info = {
        "cwd": os.getcwd(),
        "sys_path_0": sys.path[0],
        "env_PYTHONPATH": os.getenv("PYTHONPATH"),
    }
    try:
        import numpy
        info["numpy_file"] = getattr(numpy, "__file__", "unknown")
        info["numpy_version"] = getattr(numpy, "__version__", "unknown")
    except Exception as e:
        info["numpy_error"] = str(e)
    return jsonify(info)


#### ADS ####


@app.route('/api/ads', methods=['GET'])
def get_ads():
    search_id = request.args.get("search_id", default=None, type=int)
    ads = db.load_ads('ads', search_id=search_id)
    if not ads:
        return jsonify({"message": "No ads found", "data": []}), 200
    return jsonify({"data": ads or [], "message": "ok"})

#### IMAGES ####
# Serve thumbnails from THUMBNAIL_DIR


@app.route('/api/thumbnail/<ad_id>', methods=['GET'])
def serve_thumbnail(ad_id):
    filename = f'{ad_id}.jpg'
    thumb_path = THUMBNAIL_DIR / filename
    if thumb_path.exists():
        return send_from_directory(THUMBNAIL_DIR, filename)
    else:
        print(f'❌ Thumbnail not found: {thumb_path}')
        return 'Thumbnail not found', 404

# Serve scraped gallery image from IMAGES_ROOT/<ad_id>/


@app.route('/api/gallery-image/<ad_id>/<image_index>', methods=['GET', 'HEAD'])
def serve_gallery_image(ad_id, image_index):
    filename = f"{str(image_index).zfill(2)}.jpg"
    folder = IMAGES_ROOT / ad_id
    return send_from_directory(folder, filename)

# Return the number of gallery images on disk for a specific ad_id


@app.route('/api/image-count/<ad_id>', methods=['GET'])
def image_count(ad_id):
    folder = IMAGES_ROOT / ad_id
    if not folder.exists():
        return jsonify({"count": 0})
    count = len(list(folder.glob("*.jpg")))
    return jsonify({"count": count})

# Scan single image for license plate


@app.route("/api/ocr-single/<ad_id>/<image_index>", methods=["GET"])
def ocr_single_image(ad_id, image_index):
    try:
        results = ocr_reg_plate_single(ad_id, image_index)
        return jsonify({"plates": results})
    except Exception as e:
        print(f"❌ Error in OCR route: {e}")
        return jsonify({"error": str(e)}), 500

#### MOT ####


@app.route('/api/mot_history/query', methods=['GET'])
def query_mot_history():
    try:
        reg = request.args.get("reg", "").replace(" ", "").strip()
        if not reg:
            return jsonify({'error': 'Missing registration number'}), 400
        result = get_mot_history(reg.upper())
        if 'error' in result:
            return jsonify(result), 403 if 'Forbidden' in result.get('details', '') else 500
        return jsonify(result)
    except Exception as e:
        print('❌ Internal server error in /api/mot_history:', str(e))
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500


@app.route('/api/mot_history', methods=['GET'])
def get_all_mot():
    try:
        ad_id = request.args.get('ad_id')
        if not ad_id:
            ad_id = None
            print('Fetching all MOT histories')
        else:
            print(f'Fetching MOT history for ad_id {ad_id}')
        histories = db.get_mot_histories(ad_id)
        return jsonify(histories)
    except Exception as e:
        print(f'❌ Error fetching MOT history: {e}')
        return jsonify({'error': 'Internal server error', 'details': str(e)}), 500

#### CAZ ####


@app.route('/api/check-caz', methods=['GET'])
def api_check_caz():
    reg = request.args.get('reg')
    if not reg:
        return jsonify({'error': 'Missing registration'}), 400
    try:
        result = check_caz(reg)
        db.save_caz_data(reg, result)
        return jsonify({'registration': reg.upper(), 'zone': result})
    except Exception as e:
        print(f'❌ CAZ check failed for {reg}: {e}')
        return jsonify({'error': str(e)}), 500


@app.route("/api/caz", methods=["GET"])
def get_caz():
    reg = request.args.get("reg")
    if not reg:
        return jsonify({"error": "Missing registration"}), 400
    try:
        results = db.get_caz_data(reg)
        return jsonify({"registration": reg.upper(), "zone": results})
    except Exception as e:
        print(f"❌ Failed to load CAZ from DB: {e}")
        return jsonify({"error": str(e)}), 500

#### SEARCH PROFILES ####


@app.route("/api/search-profile/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):
    profile = db.get_search_profiles(profile_id)
    if profile:
        return jsonify(profile)
    return jsonify({"error": "Profile not found"}), 404


@app.route("/api/search-profiles", methods=["GET"])
def get_all_profiles():
    profiles = db.get_search_profiles()
    return jsonify({"profiles": profiles})

#### STATUSES ####


@app.route('/api/download-progress/<ad_id>', methods=['GET'])
def get_download_progress(ad_id):
    return jsonify(download_status.get(ad_id, {'status': 'Idle', 'current': 0, 'total': 0}))


@app.route('/api/scrape-progress/<int:profile_id>', methods=['GET'])
def get_scrape_progress(profile_id):
    return jsonify(scrape_progress.get(profile_id, {"status": "Idle"}))

# %% POST
# -------

#### ADS ####


@app.route('/api/fav_exc', methods=['POST'])
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
        column = 'favourited'
    elif operation == 'exclude':
        column = 'excluded'
    else:
        return jsonify({'error': f"Invalid operation '{operation}'. Must be either 'favourite' or 'exclude'"}), 400

    db.update_flag(ad_id, column, value, TABLE_NAME)
    return jsonify({"status": "ok", "ad_id": ad_id, column: value})

#### MOT ####


@app.route('/api/mot_history', methods=['POST'])
def save_mot_entry():
    data = request.get_json()
    reg = data.get('registration')
    mot_data = data.get('data')
    ad_id = data.get('ad_id')
    if not reg or not mot_data:
        return jsonify({'error': 'Missing registration or MOT data'}), 400
    db.save_mot_history(reg, mot_data, ad_id)
    return jsonify({'status': 'saved'})


@app.route('/api/mot_history/bind', methods=['POST'])
def bind_mot_entry():
    data = request.get_json()
    reg = data.get('registration')
    ad_id = data.get('ad_id')

    if not reg:
        return jsonify({'error': 'Missing registration or ad_id'}), 400
    print(f"🔗 Binding reg {reg} to ad_id {ad_id}")

    if ad_id == "":
        ad_id = None

    db.bind_mot_to_ad(reg, ad_id)
    return jsonify({'status': 'bound'})

#### IMAGES ####
# Download gallery images for a specific ad to IMAGES_ROOT by scraping the gallery page.


@app.route('/api/download-pictures', methods=['POST'])
def api_download_pictures():
    data = request.get_json()
    ad_id = data.get('ad_id')
    ad_url = data.get('ad_url')

    image_dir = IMAGES_ROOT / ad_id
    if image_dir.exists() and any(image_dir.glob('*.jpg')):
        count = len(list(image_dir.glob("*.jpg")))
        print(
            f'Skipping download. Images already exist for {ad_id} ({count} images)')
        download_status[ad_id] = {
            'status': 'Complete.', 'current': count, 'total': count}
        return jsonify({'success': True, 'skipped': True})

    download_status[ad_id] = {
        'status': 'Starting...', 'current': 0, 'total': 0}

    def progress_callback(current=None, total=None):
        if not isinstance(download_status.get(ad_id), dict):
            print(f"❌ WARNING: download_status[{ad_id}] corrupted. Resetting.")
        if not isinstance(download_status.get(ad_id), dict):
            download_status[ad_id] = {
                'status': 'Starting...', 'current': 0, 'total': 0}
        if isinstance(current, str):
            download_status[ad_id]['status'] = current
        elif current is not None and total is not None:
            download_status[ad_id]['current'] = current
            download_status[ad_id]['total'] = total
            if 'Downloading' in download_status[ad_id].get('status', ''):
                download_status[ad_id]['status'] = f'Downloading {current}/{total}...'

    def run_download():
        try:
            download_pictures(
                ad_id, ad_url, progress_callback=progress_callback)
        finally:
            total = download_status[ad_id].get('total', 1)
            download_status[ad_id] = {
                'status': 'Complete.', 'current': total, 'total': total}

    threading.Thread(target=run_download, daemon=True).start()
    return jsonify({'success': True})

#### SEARCH PROFILES ####


@app.route("/api/generate-search-url", methods=["POST"])
def api_generature_url():
    data = request.get_json()
    try:
        url = generate_autotrader_url(data)
        return jsonify({"url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/save-search-profile", methods=["POST"])
def save_search_profile():
    data = request.get_json()
    name = data.get("name")
    params = data.get("params")
    url = data.get("generated_url")
    existing_param_profile = db.search_profile_exists(params)

    if not name or not params:
        return jsonify({"error": "Missing name or params"}), 400

    if existing_param_profile:
        return jsonify({"error": f"Profile already exists", "name": existing_param_profile}), 409

    last_row = db.save_search_params(name, params, url)
    return jsonify({"status": "saved", "id": last_row})


@app.route("/api/run-scraper/<int:profile_id>", methods=["POST"])
def run_scraper(profile_id):
    profile = db.get_search_profiles(profile_id)
    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    url = profile.get('url')
    search_id = profile.get('id')

    scrape_progress[profile_id] = {"status": "Starting scraper..."}
    abort_event = threading.Event()
    scrape_abort_flags[profile_id] = abort_event

    def update_status(status):
        scrape_progress[profile_id] = {"status": status}

    def run():
        try:
            update_status("Launching browser...")
            df = scrape_autotrader(url, search_id=search_id, max_scrolls=9_999_999,
                                   status_callback=update_status, abort_event=abort_event)
            if df is None:
                update_status("Scraping aborted.")
            else:
                df['search_id'] = search_id
                update_status(f"Saving {len(df)} ads to database...")
                db.save_ads_data(df, 'ads')
                update_status(f"{len(df)} ads saved to the database.")
        finally:
            update_status("Complete.")

            def cleanup():
                time.sleep(3)
                scrape_progress.pop(profile_id, None)
                scrape_threads.pop(profile_id, None)
                scrape_abort_flags.pop(profile_id, None)
            threading.Thread(target=cleanup, daemon=True).start()

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    scrape_threads[profile_id] = thread
    return jsonify({"message": f"Scraping started for profile {profile['name']}"})


@app.route("/api/cancel-scraper/<int:profile_id>", methods=["POST"])
def cancel_scraper(profile_id):
    print("Cancelling!")
    flag = scrape_abort_flags.get(profile_id)
    thread = scrape_threads.get(profile_id)
    if not flag or not thread:
        return jsonify({"error": "No running scraper for this profile"}), 400
    flag.set()
    return jsonify({"message": "Scrape cancelled."})

# %% DELETE
# ---------


@app.route('/api/mot_history/<reg>', methods=['DELETE'])
def delete_mot_entry(reg):
    db.delete_mot_history(reg)
    return jsonify({'status': 'deleted'})


@app.route("/api/delete-search-profile/<int:profile_id>", methods=["DELETE"])
def delete_search_profile(profile_id):
    db.delete_profile(profile_id)
    db.delete_ads_by_search_id(profile_id)
    return jsonify({"message": "Profile and associated as deleted successfully"}), 200


# --- Local dev only ------------------------------------------------
if __name__ == '__main__':
    # Local dev: SQLite under ./data, create folders & tables, run Flask
    (DATA_DIR / "images").mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "thumbnails").mkdir(parents=True, exist_ok=True)
    db.create_ads_table(TABLE_NAME)
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5001")), debug=True)
