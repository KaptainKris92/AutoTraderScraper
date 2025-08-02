from utils.general_utils import extract_post_date
from utils.database_utils import check_ad_id_exists, get_saved_ad_ids, delete_ads, load_ads
from selenium_stealth import stealth
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
import pandas as pd
import os
import time
import re
import requests
import hashlib
from datetime import datetime
from pathlib import Path

# Silence warnings/errors
# Silence Tensorflow warnings: 0 = all logs, 1 = filter INFO, 2 = filter WARNING, 3 = filter ERROR
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'


# Database functions

# TODO: Avoid needing these parameters here. Add to scraper.py instead, or when implementing changing search filters
# With filters: Under £5k, within 50 miles of Caerphilly, Automatic transmission, <125k miles
AUTOTRADER_URL = 'https://www.autotrader.co.uk/car-search?maximum-mileage=125000&postcode=CF83%208TF&price-to=5000&radius=50&sort=relevance&transmission=Automatic'
DEFAULT_MAX_SCROLLS = 1  # Maybe default should be all ads possible?
TABLE_NAME = 'ads'
DATA_DIR = Path('data')

# %% General scraping functions
# ------------------


def create_stealth_driver(headless=True, url=AUTOTRADER_URL):
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--log-level-3")  # Suppresses all but fatal logs
    options.add_argument("--disable-logging")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument(
        "--disable-features=UseModernMediaControls,SyncService")
    options.add_argument("--disable-gl-drawing-for-tests")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(ChromeDriverManager().install(), log_path=os.devnull)
    driver = webdriver.Chrome(service=service, options=options)

    # Apply stealth settings
    stealth(driver,
            languages=["en-GB", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )

    driver.get(url)

    return driver


def reject_cookies(driver, timeout=15):
    try:
        # Wait for iframe containing the cookie modal
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "iframe[src*='consent']"))
        )
        iframe = driver.find_element(By.CSS_SELECTOR, "iframe[src*='consent']")
        driver.switch_to.frame(iframe)

        # Wait for the Reject All button inside the iframe
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'Reject All')]"))
        )
        reject_button = driver.find_element(
            By.XPATH, "//button[contains(text(), 'Reject All')]")
        driver.execute_script("arguments[0].click();", reject_button)
        print("✅ Clicked 'Reject All' cookie button inside iframe.")

        # Important: switch back to main content
        driver.switch_to.default_content()

    except Exception as e:
        print("⚠️ Failed to handle cookie popup:", e)

# %% AutoTrader ads
# --------------


def scrape_autotrader(url, search_id=None, save_to_excel=True, max_scrolls=DEFAULT_MAX_SCROLLS, status_callback=None, abort_event=None):

    if abort_event and abort_event.is_set():
        if status_callback:
            status_callback("Aborted.")
        return None

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if not url:
        return None

    if status_callback:
        status_callback("Opening AutoTrader...")

    driver = create_stealth_driver(headless=True, url=url)

    if abort_event and abort_event.is_set():
        driver.quit()
        return None

    if status_callback:
        status_callback("Rejecting cookies...")
    reject_cookies(driver)
    time.sleep(3)  # Give the page time to render listings

    # Wait until at least one car listing is loaded
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[data-testid='advertCard']"))
        )
    except:
        print("Couldn't find any listings.")
        driver.quit()
        return

    if status_callback:
        status_callback(f"Loading ads for up to {max_scrolls} scrolls")

    # Scroll to bottom until no new content appears (stop at MAX_SCROLLS)
    scroll_pause_time = 2.5

    for i in range(max_scrolls):
        if abort_event and abort_event.is_set():
            break

        driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);")

        prev_count = len(driver.find_elements(
            By.CSS_SELECTOR, "div[data-testid='advertCard']"))
        time.sleep(scroll_pause_time)
        new_count = len(driver.find_elements(
            By.CSS_SELECTOR, "div[data-testid='advertCard']"))

        if new_count == prev_count:
            print(f"🔄 No new listings detected after scroll #{i+1}. Stopping.")
            break

    listings = driver.find_elements(
        By.CSS_SELECTOR, "div[data-testid='advertCard']")

    total_listings = len(listings)
    print(f"Found {total_listings} listings.")
    if status_callback:
        status_callback(
            f"Found {total_listings} listings.")

    car_data = []
    live_ad_ids = set()

    # Extract listings info
    for i, listing in enumerate(listings, 1):
        if abort_event and abort_event.is_set():
            break

        def safe_find(selector, attr="text", default=""):
            try:
                el = listing.find_element(By.CSS_SELECTOR, selector)
                return el.get_attribute(attr) if attr != "text" else el.text.strip()
            except:
                return default

        href = safe_find("a[data-testid='search-listing-title']", "href")

        # Skip promoted ads
        if "journey=PROMOTED_LISTING_JOURNEY" in href:
            print(f"⛔ Skipping promoted ad: {href}")
            continue

        ad_url = f"https://www.autotrader.co.uk{href.split('?')[0]}" if href.startswith(
            "/") else href

        match = re.search(r"/(\d{15,})", ad_url)  # Matches a long numeric ID

        if match:
            ad_id = match.group(1)
        else:
            print(f"⚠️ Could not extract ad_id from URL: {ad_url}")
            continue

        # Add to live_ads to avoid deleting existing ads that have been skipped
        live_ad_ids.add(ad_id)

        # Check if ad already exists in DB
        ad_exists = check_ad_id_exists(ad_id, TABLE_NAME)

        # Skip saving ad if it already exists
        if ad_exists:
            print(f"🟡 Ad {ad_id} already in DB — skipping full scrape.")
            continue

        # Evaluate thumbnail
        thumb_url = safe_find("img.main-image", "src")
        thumb_path = Path("thumbnails") / f"{ad_id}.jpg"

        if thumb_url:
            if not thumb_path.exists():
                print(f"📸 Downloading missing thumbnail for {ad_id}")
                if status_callback:
                    status_callback(
                        f"Downloading thumbnail for ad {i} of {total_listings}.")
                download_thumbnail(ad_id, thumb_url)
            else:
                print(f"✅ Thumbnail exists for {ad_id}, skipping download.")
        else:
            print(f"⚠️ No thumbnail URL for {ad_id}")

        try:
            post_date = extract_post_date(ad_url)
        except:
            post_date = ""

        title = safe_find("[data-testid='search-listing-title']")
        subtitle = safe_find("[data-testid='search-listing-subtitle']")
        price = safe_find("div[class*='at__sc-u4ap7c-12'] span")
        mileage_raw = safe_find("[data-testid='mileage']")
        reg_year = safe_find("[data-testid='registered_year']")
        location = safe_find("[data-testid='search-listing-location']")

        # Convert mileage to numeric
        try:
            mileage_numeric = int(mileage_raw.lower().replace(
                "miles", "").replace(",", "").strip())
        except:
            mileage_numeric = ""

        city, dist = None, None

        if (match := re.match(r"(.+?)\s*\((\d+)\s*miles\)", location)):
            city, dist = match.groups()
            dist = int(dist)

        # Remove subtitle and price from title if present
        cleaned_title = title

        for val in [subtitle, price]:
            if val in cleaned_title:
                cleaned_title = cleaned_title.replace(val, "")
        # Remove trailing newline and comma if present
        cleaned_title = re.sub(r'[\n\r]+,?$', '', cleaned_title).strip()

        # Only add cars that were not excluded (e.g. promoted listings)
        if ad_id:
            car_data.append({
                'ad_url': ad_url,
                'ad_id': ad_id,
                'title': cleaned_title,
                'subtitle': subtitle,
                'price': price,
                'mileage': mileage_numeric,
                'reg_year': reg_year,
                'distance': dist,
                'location': city,
                'post_date': post_date,
                'favourited': 0,
                'excluded': 0,
                'scrape_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'search_id': search_id
            })

    driver.quit()

    df = pd.DataFrame(car_data).drop_duplicates(subset="ad_id")

    # Remove any ads no longer listed
    saved_ad_ids = set(ad['ad_id'] for ad in load_ads(
        TABLE_NAME, search_id=search_id))
    to_remove = saved_ad_ids - live_ad_ids

    if to_remove:
        print(f'🗑️ Removing {len(to_remove)} ads no longer listed.')

        if status_callback:
            status_callback(
                f"Removing {len(to_remove)}ads that have been unlisted.")
        delete_ads(to_remove, TABLE_NAME)

        # Remove associated thumbnail and image folders
        for ad_id in to_remove:
            if abort_event and abort_event.is_set():
                break

            thumb = Path("thumbnails") / f"{ad_id}.jpg"
            image_folder = Path("images") / ad_id

            if thumb.exists():
                thumb.unlink(missing_ok=True)
                if status_callback:
                    status_callback(f"Deleted thumbnail for {ad_id}")
                print(f"🗑️ Deleted thumbnail for {ad_id}")

            if image_folder.exists():
                for file in image_folder.glob("*"):
                    file.unlink()
                image_folder.rmdir()
                if status_callback:
                    status_callback(f"Deleted image folder for {ad_id}")
                print(f"🗑️ Deleted image folder for {ad_id}")

    if save_to_excel:
        file_path = DATA_DIR / f"cars_{datetime.now().date()}.xlsx"
        df.to_excel(file_path, index=False)
        print(f"Saved {len(df)} listings to {file_path}")

    if status_callback:
        status_callback("Complete.")

    return df

# %% AutoTrader images
# ---------------------


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


def download_thumbnail(ad_id, thumbnail_url, save_dir='thumbnails'):
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(thumbnail_url, timeout=10)
        if response.status_code == 200:
            save_path = Path(save_dir) / f"{ad_id}.jpg"
            with open(save_path, 'wb') as f:
                f.write(response.content)
            print(f'✅ Saved thumbnail to {save_path}')
        else:
            print(
                f'❌ Failed to download image for {ad_id}, status {response.status_code}')
    except Exception as e:
        print(f"❌ Error downloading thumbnail for {ad_id}: {e}")


def download_missing_images(limit=None):
    ad_ids = get_saved_ad_ids()

    # Maybe sort according to time saved
    if limit:
        ad_ids = ad_ids[:limit]

    for ad_id, ad_url in ad_ids:

        if not ad_url or not ad_id:
            print(f'⚠️ Skipping entry with missing ad_id or ad_url')
            continue

        folder = Path("images") / ad_id

        if (folder / "01.jpg").exists():
            print(f'✅ Images already downloaded for {ad_id}. Skipping.')
            continue

        print(f'Downloading images for {ad_id}')
        try:
            download_pictures(ad_id, ad_url)
        except Exception as e:
            print(f'❌ Error downloading for {ad_id}: {e}')
            with open('failed_downloads.log', 'a', encoding='utf-8') as log:
                log.write(f'{ad_id}, {ad_url}\n')


def download_pictures(ad_id, ad_url, progress_callback=None):
    folder = Path("images") / ad_id
    folder.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback('Launching browser...')
    driver = create_stealth_driver(headless=True, url=ad_url)

    if progress_callback:
        progress_callback('Rejecting cookies...')
    reject_cookies(driver)

    try:
        if progress_callback:
            progress_callback('Clicking ad image thumbnail...')

        time.sleep(1)

        # Click a thumbnail on ad page instead of the 'View gallery' button
        thumb = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button[data-testid^='open-carousel']"))
        )
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", thumb)
        time.sleep(0.5)

        # Check for overlays
        driver.execute_script("window.scrollBy(0, -100);")  # Nudge view up
        WebDriverWait(driver, 5).until(EC.visibility_of(thumb))

        # Click via JS to bypass any overlays
        driver.execute_script('arguments[0].click();', thumb)

        print(f"✅ Clicked thumbnail to open gallery for {ad_id}")

    except Exception as e:
        print(f"⚠️ Failed to click thumbnail for {ad_id}: {e}")
        driver.save_screenshot(f"screenshots/error_click_{ad_id}.png")
        driver.quit()
        return

    # Extract image URLs
    try:
        if progress_callback:
            progress_callback('Extracting image URLs...')

        # Wait for modal to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, "div[role='dialog'] img"))
        )

        time.sleep(1)  # Ensure images fully render

        image_elements = driver.find_elements(
            By.CSS_SELECTOR, "div[role='dialog'] picture source")

        srcset_urls = []
        for elem in image_elements:
            srcset = elem.get_attribute('srcset')
            if srcset:
                urls = [s.strip().split(" ")[0]
                        for s in srcset.split(",") if "media" in s]
                srcset_urls.extend(urls)

        img_urls = extract_highest_res_images(srcset_urls)

        if progress_callback:
            progress_callback(0, len(img_urls))

        if not img_urls:
            print("⚠️ No modal image URLs found, falling back to thumbnails.")
            thumb_elements = driver.find_elements(
                By.CSS_SELECTOR, "img.ImageGalleryImage__image")
            img_urls = list({
                img.get_attribute("src")
                for img in thumb_elements
                if img.get_attribute("src") and "media" in img.get_attribute("src")
            })

    except Exception as e:
        print(f"⚠️ Could not extract image URLs for {ad_id}: {e}")
        img_urls = []

    total_images = len(img_urls)

    if progress_callback:
        progress_callback(f'Downloading {total_images} image(s)...')

    # Download images with progress
    for i, img_url in enumerate(img_urls):
        try:
            img_data = requests.get(img_url, timeout=10).content
            with open(folder / f"{i+1:02}.jpg", "wb") as f:
                f.write(img_data)

            # Call progress callback to get how many images downloaded out of total
            if progress_callback:
                progress_callback(i + 1, total_images)

        except Exception as e:
            print(f"❌ Failed to download image {i+1} for {ad_id}: {e}")

    driver.quit()
    print(f"✅ Downloaded {len(img_urls)} images for {ad_id}")

# %% CAZ
# -------


def check_caz(registration="FL56DPZ"):
    driver = create_stealth_driver(
        headless=True, url="https://multiple-vehiclecheck-pay.drive-clean-air-zone.service.gov.uk/what_would_you_like_to_do")

    try:
        wait = WebDriverWait(driver, 15)
        driver.get(
            "https://multiple-vehiclecheck-pay.drive-clean-air-zone.service.gov.uk/what_would_you_like_to_do")
        time.sleep(2)

        # Step 1: Choose "Check a vehicle" and Continue
        print('Page 1')
        try:
            # print('Finding "Check a vehicle" radio button...')
            check_vehicle_label = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//label[strong[text()='Check a vehicle']]"))
            )
            check_vehicle_label.click()
            # print('✔ Selected "Check a vehicle".')
        except Exception as e:
            # print("❌ Could not find or click 'check-a-vehicle'")
            # with open("debug_page.html", "w", encoding="utf-8") as f:
            #     f.write(driver.page_source)
            raise e

        try:
            # print('Finding "Continue" button...')
            wait.until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "input[type='submit']"))).click()
            # print('✔ Clicked "Continue".')
        except Exception as e:
            # print("❌ Could not find or click 'Continue' button")
            # with open("debug_page.html", "w", encoding="utf-8") as f:
            #     f.write(driver.page_source)
            raise e

        time.sleep(2)

        # Step 2: Enter registration number and select 'UK'
        print('Page 2')
        try:
            # print('Trying to enter registration...')
            wait.until(EC.presence_of_element_located(
                (By.ID, "vrn"))).send_keys(registration)
            # print('✔ Registration entered. Trying to find "UK" radio button')
            driver.find_element(
                By.ID, "registration-country-1").click()  # UK is default
            # print('✔ "UK" radio button selected. Trying to find "Continue" button')
            driver.find_element(
                By.CSS_SELECTOR, "input[type='submit']").click()
            # print('✔ "Continue" button clicked')
        except Exception as e:
            # print("❌ Could not enter reg, select 'UK' or click 'Continue' button")
            # with open("debug_page.html", "w", encoding="utf-8") as f:
            #     f.write(driver.page_source)
            raise e

        # Step 3: Confirm vehicle details
        print('Page 3')
        try:
            wait.until(EC.presence_of_element_located(
                (By.ID, "confirm_details-1")))
            # print('Finding "Yes" radio button...')
            confirm_radio = driver.find_element(By.ID, "confirm_details-1")
            driver.execute_script("arguments[0].click();", confirm_radio)
            # print('✔ "Yes" confirmation selected. Finding "Confirm" button.')
            driver.find_element(
                By.CSS_SELECTOR, "input[type='submit']").click()
            # print('✔ "Confirm" button clicked.')
        except Exception as e:
            # print("❌ Could not confirm details")
            # with open("debug_page.html", "w", encoding="utf-8") as f:
            #     f.write(driver.page_source)
            raise e

        # Step 4: Scrape results table
        print('Page 4 (Final)')

        try:
            wait.until(EC.presence_of_element_located(
                (By.ID, "compliance-table")))
            rows = driver.find_elements(
                By.CSS_SELECTOR, "#compliance-table tbody tr")

            results = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                results.append({
                    "Zone": cols[0].text.strip(),
                    "Daily Charge": cols[1].text.strip(),
                    "Zone Live": cols[2].text.strip(),
                    "Map URL": cols[3].find_element(By.TAG_NAME, "a").get_attribute("href"),
                    "Exemptions URL": cols[4].find_element(By.TAG_NAME, "a").get_attribute("href")
                })
        except Exception as e:
            print("❌ Could not scrape results table")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise e

        return results

    finally:
        driver.quit()


if __name__ == '__main__':
    from database_utils import check_ad_id_exists, get_saved_ad_ids, delete_ads, load_ads
    from general_utils import extract_post_date
    from pprint import pprint
    pprint(check_caz())
