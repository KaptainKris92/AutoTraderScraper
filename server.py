from flask import Flask, request, jsonify, send_from_directory
from utils.database_utils import (
    create_ads_table,
    update_flag,
    load_ads,
    save_mot_history,
    get_mot_histories,
    delete_mot_history,
    bind_mot_to_ad,
    ensure_tables_exist,
    save_caz_data,
    get_caz_data,
    save_search_params,
    get_search_profiles,
    search_profile_exists,
    save_ads_data,
    delete_profile,
    delete_ads_by_search_id,
    sync_search_profile_ads,
)
from utils.mot_history import get_mot_history
from utils.scrape_utils import download_pictures, check_caz, scrape_autotrader
from utils.search_utils import generate_autotrader_url
from pathlib import Path
from utils.image_ocr import ocr_reg_plate_single
import threading
import time

app = Flask(__name__)
TABLE_NAME = "ads"
THUMBNAIL_DIR = Path("thumbnails")
ensure_tables_exist()

# In-memory progress trackers

# For scraping the ads
scrape_progress = {}  # {profile_id: {"status": str}}
scrape_threads = {}  # {profile_id: threading.Thread}
scrape_abort_flags = {}  # {profile_id: threading.Event}
# For downloading gallery images
download_status = {}


# %% GET
# -------

#### ADS ####

# Returns all rows from ads table


@app.route("/api/ads", methods=["GET"])
def get_ads():
    search_id = request.args.get("search_id", default=None, type=int)

    ads = load_ads("ads", search_id=search_id)

    if not ads:
        return jsonify({"message": "No ads found", "data": []}), 200
    return jsonify({"data": ads or [], "message": "ok"})


#### IMAGES ####

# Serve thumbnails from root `thumbnails/` folder


@app.route("/api/thumbnail/<ad_id>", methods=["GET"])
def serve_thumbnail(ad_id):
    filename = f"{ad_id}.jpg"
    thumb_path = THUMBNAIL_DIR / filename

    if thumb_path.exists():
        return send_from_directory(THUMBNAIL_DIR, filename)
    else:
        print(f"❌ Thumbnail not found: {thumb_path}")
        return "Thumbnail not found", 404


# Serve scraped gallery image from root `images/` folder


@app.route("/api/gallery-image/<ad_id>/<image_index>", methods=["GET", "HEAD"])
def serve_gallery_image(ad_id, image_index):
    filename = f"{str(image_index).zfill(2)}.jpg"
    folder = Path("images") / ad_id
    return send_from_directory(folder, filename)


# Return the number of gallery images on disk for a specific ad_id


@app.route("/api/image-count/<ad_id>", methods=["GET"])
def image_count(ad_id):
    folder = Path("images") / ad_id
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
    pass


#### MOT ####

# Get new MOT History through API


@app.route("/api/mot_history/query", methods=["GET"])
def query_mot_history():
    try:
        reg = request.args.get("reg").replace(" ", "").strip()
        if not reg:
            return jsonify({"error": "Missing registration number"}), 400

        result = get_mot_history(reg.upper())

        if "error" in result:
            return jsonify(result), 403 if "Forbidden" in result.get(
                "details", ""
            ) else 500

        return jsonify(result)
    except Exception as e:
        print("❌ Internal server error in /api/mot_history:", str(e))
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


# Get previous MOT History from local database


@app.route("/api/mot_history", methods=["GET"])
def get_all_mot():
    try:
        ad_id = request.args.get("ad_id")
        if not ad_id:
            ad_id = None
            print("Fetching all MOT histories")
        else:
            print(f"Fetching MOT history for ad_id {ad_id}")

        histories = get_mot_histories(ad_id)
        return jsonify(histories)

    except Exception as e:
        print(f"❌ Error fetching MOT history: {e}")
        return jsonify({"error": "Internal server error", "details": str(e)}), 500


#### CAZ ####


# Goes through 4 CAZ pages using registration number
@app.route("/api/check-caz", methods=["GET"])
def api_check_caz():
    reg = request.args.get("reg")
    if not reg:
        return jsonify({"error": "Missing registration"}), 400

    try:
        result = check_caz(reg)
        save_caz_data(reg, result)
        return jsonify({"registration": reg.upper(), "zone": result})
    except Exception as e:
        print(f"❌ CAZ check failed for {reg}: {e}")
        return jsonify({"error": str(e)}), 500


# Gets CAZ charges data for specified registration number from local database


@app.route("/api/caz", methods=["GET"])
def get_caz():
    reg = request.args.get("reg")
    if not reg:
        return jsonify({"error": "Missing registration"}), 400
    try:
        results = get_caz_data(reg)
        return jsonify({"registration": reg.upper(), "zone": results})
    except Exception as e:
        print(f"❌ Failed to load CAZ from DB: {e}")
        return jsonify({"error": str(e)}), 500


#### SEARCH PROFILES ####

# Retrieves a single search profile


@app.route("/api/search-profile/<int:profile_id>", methods=["GET"])
def get_profile(profile_id):
    profile = get_search_profiles(profile_id)
    if profile:
        return jsonify(profile)
    return jsonify({"error": "Profile not found"}), 404


@app.route("/api/search-profiles", methods=["GET"])
def get_all_profiles():
    profiles = get_search_profiles()
    return jsonify({"profiles": profiles})


# Return `download_status`` generated by the `api_download_pictures()` route

#### STATUSES ####


@app.route("/api/download-progress/<ad_id>", methods=["GET"])
def get_download_progress(ad_id):
    return jsonify(
        download_status.get(ad_id, {"status": "Idle", "current": 0, "total": 0})
    )


# Scraping progress


@app.route("/api/scrape-progress/<int:profile_id>", methods=["GET"])
def get_scrape_progress(profile_id):
    return jsonify(scrape_progress.get(profile_id, {"status": "Idle"}))


# %% POST
# -------

#### ADS ####


# Changes value of `excluded` or `favourited` column
@app.route("/api/fav_exc", methods=["POST"])
def favourite_or_exclude_ad():
    data = request.get_json()
    ad_id = data.get("ad_id")
    operation = data.get("operation")
    value = data.get("value")
    if value is None:
        return jsonify({"error": "Missing value. Value must be 0 or 1."}), 400
    elif value not in [0, 1]:
        return jsonify({"error": "Invalid value. Value must be 0 or 1."}), 400
    else:
        value = int(value)

    if not ad_id:
        return jsonify({"error": "Missing ad_id"}), 400
    if not operation:
        return jsonify({"error": "Missing operation"}), 400

    if operation == "favourite":
        column = "favourited"
    elif operation == "exclude":
        column = "excluded"
    else:
        return jsonify(
            {
                "error": f"Invalid operation '{operation}'. Must be either 'favourite' or 'exclude'"
            }
        ), 400

    update_flag(ad_id, column, value, TABLE_NAME)
    return jsonify({"status": "ok", "ad_id": ad_id, column: value})


#### MOT ####

# Saves MOT History API results to `mot_history` table


@app.route("/api/mot_history", methods=["POST"])
def save_mot_entry():
    data = request.get_json()
    reg = data.get("registration")
    mot_data = data.get("data")
    ad_id = data.get("ad_id")
    if not reg or not mot_data:
        return jsonify({"error": "Missing registration or MOT data"}), 400
    save_mot_history(reg, mot_data, ad_id)
    return jsonify({"status": "saved"})


# Link an MOT entry to an ad_id


@app.route("/api/mot_history/bind", methods=["POST"])
def bind_mot_entry():
    data = request.get_json()
    reg = data.get("registration")
    ad_id = data.get("ad_id")

    if not reg:
        return jsonify({"error": "Missing registration or ad_id"}), 400
    print(f"🔗 Binding reg {reg} to ad_id {ad_id}")

    # Interpret empty string as NULL
    if ad_id == "":
        ad_id = None

    bind_mot_to_ad(reg, ad_id)
    return jsonify({"status": "bound"})


#### IMAGES ####

# Download gallery images for a specific ad to root `images/` folder by scraping the gallery page for highest resolution images.


@app.route("/api/download-pictures", methods=["POST"])
def api_download_pictures():
    data = request.get_json()
    ad_id = data.get("ad_id")
    ad_url = data.get("ad_url")

    image_dir = Path("images") / ad_id
    if image_dir.exists() and any(image_dir.glob("*.jpg")):
        count = len(list(image_dir.glob("*.jpg")))
        print(f"Skipping download. Images already exist for {ad_id} ({count} images)")
        download_status[ad_id] = {
            "status": "Complete.",
            "current": count,
            "total": count,
        }

        return jsonify({"success": True, "skipped": True})

    download_status[ad_id] = {"status": "Starting...", "current": 0, "total": 0}

    def progress_callback(current=None, total=None):
        if not isinstance(download_status.get(ad_id), dict):
            print(f"❌ WARNING: download_status[{ad_id}] corrupted. Resetting.")

        # Ensure structure is always a dict
        if not isinstance(download_status.get(ad_id), dict):
            download_status[ad_id] = {"status": "Starting...", "current": 0, "total": 0}

        # Status string updates
        if isinstance(current, str):
            download_status[ad_id]["status"] = current

        # Numeric progress for images (e.g. `1/10``)
        elif current is not None and total is not None:
            download_status[ad_id]["current"] = current
            download_status[ad_id]["total"] = total

            # Only update status if not already a string status
            if "Downloading" in download_status[ad_id].get("status", ""):
                download_status[ad_id]["status"] = f"Downloading {current}/{total}..."

    def run_download():
        try:
            count = download_pictures(
                ad_id,
                ad_url,
                progress_callback=progress_callback,
            )

            if count == 0:
                raise RuntimeError("No gallery images were found.")

            download_status[ad_id] = {
                "status": "Complete.",
                "current": count,
                "total": count,
            }

        except Exception as exc:
            app.logger.exception(
                "Gallery download failed for ad %s",
                ad_id,
            )

            download_status[ad_id] = {
                "status": f"Error: {exc}",
                "current": 0,
                "total": 0,
            }

    # Launch in background thread to avoid blocking Flask
    threading.Thread(target=run_download).start()

    return jsonify({"success": True})


#### SEARCH PROFILES ####


@app.route("/api/generate-search-url", methods=["POST"])
def api_generature_url():
    data = request.get_json()
    try:
        url = generate_autotrader_url(data)
        return jsonify({"url": url})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Saves user's search preferences into a profile. Ads are linked to this profile (can be linked to multiple).


@app.route("/api/save-search-profile", methods=["POST"])
def save_search_profile():
    data = request.get_json()
    name = data.get("name")
    params = data.get("params")
    url = data.get("generated_url")
    existing_param_profile = search_profile_exists(params)

    if not name or not params:
        return jsonify({"error": "Missing name or params"}), 400

    if existing_param_profile:
        return jsonify(
            {"error": f"Profile already exists", "name": existing_param_profile}
        ), 409

    last_row = save_search_params(name, params, url)
    return jsonify({"status": "saved", "id": last_row})


# Runs `scraper.py` with provided link to update databases


@app.route("/api/run-scraper/<int:profile_id>", methods=["POST"])
def run_scraper(profile_id):
    profile = get_search_profiles(profile_id)

    if not profile:
        return jsonify({"error": "Profile not found"}), 404

    existing_thread = scrape_threads.get(profile_id)

    if existing_thread and existing_thread.is_alive():
        return jsonify({"error": "A scrape is already running for this profile."}), 409

    url = profile.get("url")
    search_id = profile.get("id")

    # Initiate progress
    scrape_progress[profile_id] = {"status": "Starting scraper..."}
    abort_event = threading.Event()
    scrape_abort_flags[profile_id] = abort_event

    def update_status(status):
        scrape_progress[profile_id] = {"status": status}

    def run():
        terminal_status = "Error: scraper stopped unexpectedly."

        try:
            update_status("Launching browser...")

            df = scrape_autotrader(
                url,
                search_id=search_id,
                save_to_excel=False,
                max_scrolls=1_000,
                status_callback=update_status,
                abort_event=abort_event,
            )

            print(
                f"✅ Scraper returned {len(df)} ads "
                f"for profile {search_id}"
            )

            if abort_event.is_set():
                terminal_status = "Cancelled."
                return

            if df is None:
                terminal_status = "Error: scraper returned no result."
                return

            df["search_id"] = search_id

            update_status(f"Saving {len(df)} matching ads...")

            save_ads_data(df, TABLE_NAME)

            sync_search_profile_ads(
                search_id,
                df["ad_id"].tolist(),
            )

            print(
                f"✅ Synced {len(df)} ads "
                f"to profile {search_id}"
            )

            terminal_status = f"Complete. {len(df)} ads linked to this profile."

        except Exception as exc:
            app.logger.exception(
                "Scraping failed for profile %s",
                profile_id,
            )
            terminal_status = f"Error: {exc}"

        finally:
            update_status(terminal_status)

            def cleanup():
                # Leave errors available long enough for the UI to display them.
                delay = (
                    30 if terminal_status.startswith(("Error:", "Cancelled.")) else 5
                )
                time.sleep(delay)

                scrape_progress.pop(profile_id, None)
                scrape_threads.pop(profile_id, None)
                scrape_abort_flags.pop(profile_id, None)

            threading.Thread(
                target=cleanup,
                daemon=True,
            ).start()

    thread = threading.Thread(target=run)
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


# Delete an MOT entry
@app.route("/api/mot_history/<reg>", methods=["DELETE"])
def delete_mot_entry(reg):
    delete_mot_history(reg)
    return jsonify({"status": "deleted"})


@app.route("/api/delete-search-profile/<int:profile_id>", methods=["DELETE"])
def delete_search_profile(profile_id):
    delete_profile(profile_id)
    delete_ads_by_search_id(profile_id)
    return jsonify({"message": "Profile and associated as deleted successfully"}), 200


if __name__ == "__main__":
    create_ads_table(TABLE_NAME)
    app.run(debug=True)
