from utils.general_utils import extract_post_date
from utils.database_utils import (
    check_ad_id_exists,
    get_saved_ad_ids,
    delete_ads_by_ad_id,
    delete_ads_by_search_id,
    load_ads,
    update_search_profile_timestamp,
)
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
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


# Database functions

# TODO: Avoid needing these parameters here. Add to scraper.py instead, or when implementing changing search filters
# With filters: Under £5k, within 50 miles of Caerphilly, Automatic transmission, <125k miles
AUTOTRADER_URL = "https://www.autotrader.co.uk/car-search?maximum-mileage=125000&postcode=CF83%208TF&price-to=5000&radius=50&sort=relevance&transmission=Automatic"
DEFAULT_MAX_SCROLLS = 1  # Maybe default should be all ads possible?
TABLE_NAME = "ads"
DATA_DIR = Path("data")
LISTING_CARD_SELECTOR = "[data-testid^='advertCard']"

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
    # options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-features=UseModernMediaControls,SyncService")
    # options.add_argument("--disable-gl-drawing-for-tests")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    service = Service(ChromeDriverManager().install(), log_path=os.devnull)
    driver = webdriver.Chrome(service=service, options=options)

    # Apply stealth settings
    stealth(
        driver,
        languages=["en-GB", "en"],
        vendor="Google Inc.",
        platform="Win32",
        webgl_vendor="Intel Inc.",
        renderer="Intel Iris OpenGL Engine",
        fix_hairline=True,
    )

    driver.get(url)

    return driver


def reject_cookies(driver, timeout=5):
    """Dismiss AutoTrader cookie consent if it is shown."""

    xpaths = [
        "//button[contains(normalize-space(.), 'Essential Cookies Only')]",
        "//button[contains(normalize-space(.), 'Reject All')]",
    ]

    def try_click():
        for xpath in xpaths:
            for button in driver.find_elements(By.XPATH, xpath):
                if button.is_displayed():
                    driver.execute_script("arguments[0].click();", button)
                    print(f"✅ Clicked cookie button: {button.text}")
                    time.sleep(0.5)
                    return True

        return False

    deadline = time.time() + timeout

    # Current AutoTrader popup: main document.
    while time.time() < deadline:
        if try_click():
            return
        time.sleep(0.25)

    # Older AutoTrader popup: iframe.
    for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
        try:
            driver.switch_to.frame(iframe)

            if try_click():
                return
        finally:
            driver.switch_to.default_content()

    print("ℹ️ No cookie popup found.")


# %% AutoTrader ads
# --------------


def scrape_autotrader(
    url,
    search_id=None,
    save_to_excel=True,
    max_scrolls=DEFAULT_MAX_SCROLLS,
    status_callback=None,
    abort_event=None,
):

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
            EC.presence_of_element_located((By.CSS_SELECTOR, LISTING_CARD_SELECTOR))
        )
    except Exception as exc:
        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = (
            screenshot_dir / f"scrape_no_listings_{search_id or 'unknown'}.png"
        )
        driver.save_screenshot(str(screenshot_path))
        driver.quit()

        raise RuntimeError(
            "No AutoTrader listing cards were found. "
            "The search may have no results, AutoTrader may have changed its "
            "markup, or the browser may have been blocked. "
            f"Screenshot saved to {screenshot_path}."
        ) from exc

    if status_callback:
        status_callback("Loading all available listings...")

    # Scroll to bottom until no new content appears (stop at MAX_SCROLLS)
    scroll_pause_time = 2.5
    stable_scrolls = 0
    max_seen = len(
        driver.find_elements(
            By.CSS_SELECTOR,
            LISTING_CARD_SELECTOR,
        )
    )
    started_at = time.monotonic()

    for i in range(max_scrolls):
        if abort_event and abort_event.is_set():
            break

        if time.monotonic() - started_at > 180:
            raise RuntimeError("Timed out while loading AutoTrader listings.")

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)

        new_count = len(
            driver.find_elements(
                By.CSS_SELECTOR,
                LISTING_CARD_SELECTOR,
            )
        )

        if new_count > max_seen:
            max_seen = new_count
            stable_scrolls = 0
        else:
            stable_scrolls += 1

        if status_callback:
            status_callback(f"Loading listings... {max_seen} found (scroll {i + 1})")

        if stable_scrolls >= 2:
            print(
                f"🔄 No additional listings after {stable_scrolls} scrolls. Stopping."
            )
            break

    listings = driver.find_elements(By.CSS_SELECTOR, LISTING_CARD_SELECTOR)

    total_listings = len(listings)
    print(f"Found {total_listings} listings.")
    if status_callback:
        status_callback(f"Found {total_listings} listings.")

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

        ad_url = (
            f"https://www.autotrader.co.uk{href.split('?')[0]}"
            if href.startswith("/")
            else href
        )

        match = re.search(r"/(\d{15,})", ad_url)  # Matches a long numeric ID

        if match:
            ad_id = match.group(1)
        else:
            print(f"⚠️ Could not extract ad_id from URL: {ad_url}")
            continue

        # Add to live_ads to avoid deleting existing ads that have been skipped
        live_ad_ids.add(ad_id)

        # Evaluate thumbnail
        thumb_url = safe_find("img", "src") or safe_find("img", "data-src")
        thumb_path = Path("thumbnails") / f"{ad_id}.jpg"

        if thumb_url:
            if not thumb_path.exists():
                print(f"📸 Downloading missing thumbnail for {ad_id}")
                if status_callback:
                    status_callback(
                        f"Downloading thumbnail for ad {i} of {total_listings}."
                    )
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

        price_match = re.search(r"£[\d,]+", title)
        price = price_match.group(0) if price_match else ""
        mileage_raw = safe_find("[data-testid='mileage']")
        reg_year = safe_find("[data-testid='registered_year']")
        location = safe_find("[data-testid='search-listing-location']")

        # Convert mileage to numeric
        try:
            mileage_numeric = int(
                mileage_raw.lower().replace("miles", "").replace(",", "").strip()
            )
        except:
            mileage_numeric = ""

        city, dist = None, None

        if match := re.match(r"(.+?)\s*\((\d+)\s*miles\)", location):
            city, dist = match.groups()
            dist = int(dist)

        # Remove subtitle and price from title if present
        cleaned_title = title

        for val in [subtitle, price]:
            if val in cleaned_title:
                cleaned_title = cleaned_title.replace(val, "")
        # Remove trailing newline and comma if present
        cleaned_title = re.sub(r"[\n\r]+,?$", "", cleaned_title).strip()

        # Only add cars that were not excluded (e.g. promoted listings)
        if ad_id:
            car_data.append(
                {
                    "ad_url": ad_url,
                    "ad_id": ad_id,
                    "title": cleaned_title,
                    "subtitle": subtitle,
                    "price": price,
                    "mileage": mileage_numeric,
                    "reg_year": reg_year,
                    "distance": dist,
                    "location": city,
                    "post_date": post_date,
                    "favourited": 0,
                    "excluded": 0,
                    "scrape_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "search_id": search_id,
                }
            )

    driver.quit()

    df = pd.DataFrame(car_data).drop_duplicates(subset="ad_id")

    if save_to_excel:
        file_path = DATA_DIR / f"cars_{datetime.now().date()}.xlsx"
        df.to_excel(file_path, index=False)
        print(f"Saved {len(df)} listings to {file_path}")

    if search_id:
        update_search_profile_timestamp(search_id)

    return df


# %% AutoTrader images
# ---------------------


def extract_highest_res_images(urls):
    """Return the highest-width version of each image URL."""
    best_images = {}

    for url in urls:
        if not url:
            continue

        clean_url = url.split("?")[0]
        width_match = re.search(r"/w(\d+)/", clean_url)
        width = int(width_match.group(1)) if width_match else 0

        # Treat URLs differing only by /wNNN/ as the same image.
        key = re.sub(r"/w\d+/", "/w{width}/", clean_url)

        if key not in best_images or width > best_images[key][0]:
            best_images[key] = (width, url)

    return [url for _, url in best_images.values()]


def download_thumbnail(ad_id, thumbnail_url, save_dir="thumbnails"):
    Path(save_dir).mkdir(parents=True, exist_ok=True)
    try:
        response = requests.get(thumbnail_url, timeout=10)
        if response.status_code == 200:
            save_path = Path(save_dir) / f"{ad_id}.jpg"
            with open(save_path, "wb") as f:
                f.write(response.content)
            print(f"✅ Saved thumbnail to {save_path}")
        else:
            print(
                f"❌ Failed to download image for {ad_id}, status {response.status_code}"
            )
    except Exception as e:
        print(f"❌ Error downloading thumbnail for {ad_id}: {e}")


def download_missing_images(limit=None):
    ad_ids = get_saved_ad_ids()

    # Maybe sort according to time saved
    if limit:
        ad_ids = ad_ids[:limit]

    for ad_id, ad_url in ad_ids:
        if not ad_url or not ad_id:
            print(f"⚠️ Skipping entry with missing ad_id or ad_url")
            continue

        folder = Path("images") / ad_id

        if (folder / "01.jpg").exists():
            print(f"✅ Images already downloaded for {ad_id}. Skipping.")
            continue

        print(f"Downloading images for {ad_id}")
        try:
            download_pictures(ad_id, ad_url)
        except Exception as e:
            print(f"❌ Error downloading for {ad_id}: {e}")
            with open("failed_downloads.log", "a", encoding="utf-8") as log:
                log.write(f"{ad_id}, {ad_url}\n")


def download_pictures(ad_id, ad_url, progress_callback=None):
    folder = Path("images") / ad_id
    folder.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback("Launching browser...")
    driver = create_stealth_driver(headless=True, url=ad_url)

    if progress_callback:
        progress_callback("Rejecting cookies...")
    reject_cookies(driver, timeout=3)

    try:
        if progress_callback:
            progress_callback("Clicking ad image thumbnail...")

        time.sleep(1)

        # Click a thumbnail on ad page instead of the 'View gallery' button
        gallery_selectors = [
            "button[data-testid*='carousel']",
            "button[data-testid*='gallery']",
            "[data-testid*='gallery'] button",
            "button[aria-label*='image' i]",
            "button[aria-label*='photo' i]",
        ]

        thumb = None

        for selector in gallery_selectors:
            try:
                thumb = WebDriverWait(driver, 2).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                print(f"✅ Found gallery control with selector: {selector}")
                break
            except Exception:
                continue

        # Fall back to finding an image and its clickable parent.
        if thumb is None:
            images = driver.find_elements(By.CSS_SELECTOR, "main img, picture img")

            for image in images:
                clickable = driver.execute_script(
                    """
                    return arguments[0].closest(
                        'button, a, [role="button"]'
                    );
                    """,
                    image,
                )

                if clickable:
                    thumb = clickable
                    print("✅ Found gallery control via clickable image.")
                    break
        test_ids = driver.execute_script(
            """
            return [...document.querySelectorAll('[data-testid]')]
                .map(el => ({
                    tag: el.tagName,
                    testid: el.getAttribute('data-testid'),
                    aria: el.getAttribute('aria-label')
                }))
                .filter(x =>
                    /image|photo|gallery|carousel/i.test(
                        `${x.testid || ''} ${x.aria || ''}`
                    )
                );
            """
        )

        print("🔎 Gallery-related elements found:")
        for item in test_ids:
            print(item)

        if thumb is None:
            raise RuntimeError(
                "Could not find a gallery control on the AutoTrader advert page."
            )
        driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", thumb
        )
        time.sleep(0.5)

        # Check for overlays
        driver.execute_script("window.scrollBy(0, -100);")  # Nudge view up
        WebDriverWait(driver, 5).until(EC.visibility_of(thumb))

        # Click via JS to bypass any overlays
        driver.execute_script("arguments[0].click();", thumb)

        print(f"✅ Clicked thumbnail to open gallery for {ad_id}")

    except Exception as exc:
        screenshot_dir = Path("screenshots")
        screenshot_dir.mkdir(parents=True, exist_ok=True)

        screenshot_path = screenshot_dir / f"error_click_{ad_id}.png"
        driver.save_screenshot(str(screenshot_path))
        driver.quit()

        raise RuntimeError(
            f"Could not open AutoTrader image gallery. "
            f"Screenshot saved to {screenshot_path}."
        ) from exc

    # Extract AutoTrader image URLs from the rendered page.
    try:
        if progress_callback:
            progress_callback("Extracting image URLs...")

        time.sleep(1)

        candidate_urls = []

        # Current rendered <img> and <source> elements.
        elements = driver.find_elements(
            By.CSS_SELECTOR,
            "img[src], img[srcset], source[srcset]",
        )

        for element in elements:
            for attr in ("src", "srcset"):
                value = element.get_attribute(attr)

                if not value:
                    continue

                for candidate in value.split(","):
                    url = candidate.strip().split()[0]

                    if "m.atcdn.co.uk/a/media/" in url:
                        candidate_urls.append(url)

        # AutoTrader also embeds media URLs in the page's application data.
        page_source = driver.page_source.replace("\\/", "/").replace("&amp;", "&")

        embedded_urls = re.findall(
            r"https://m\.atcdn\.co\.uk/a/media/"
            r"(?:w\d+|\{resize\})/"
            r"[a-f0-9]+\.jpg",
            page_source,
            flags=re.IGNORECASE,
        )

        candidate_urls.extend(embedded_urls)

        # Convert every URL to a consistent high-resolution URL and deduplicate
        # by image ID while preserving order.
        img_urls = []
        seen_ids = set()

        for url in candidate_urls:
            match = re.search(
                r"/([a-f0-9]+)\.jpg(?:\?|$)",
                url,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            image_id = match.group(1).lower()

            if image_id in seen_ids:
                continue

            seen_ids.add(image_id)

            img_urls.append(f"https://m.atcdn.co.uk/a/media/w1200/{image_id}.jpg")

        print(f"📸 Found {len(img_urls)} unique AutoTrader images.")

        if not img_urls:
            raise RuntimeError(
                "No AutoTrader image URLs were found on the advert page."
            )

    except Exception as exc:
        driver.quit()
        raise RuntimeError(
            "Could not extract image URLs from the AutoTrader advert."
        ) from exc

    total_images = len(img_urls)

    if total_images == 0:
        driver.quit()
        raise RuntimeError(
            "The AutoTrader gallery opened, but no image URLs were found."
        )

    if progress_callback:
        progress_callback(f"Downloading {total_images} image(s)...")

    # Download images with progress
    for i, img_url in enumerate(img_urls):
        try:
            img_data = requests.get(img_url, timeout=10).content
            with open(folder / f"{i + 1:02}.jpg", "wb") as f:
                f.write(img_data)

            # Call progress callback to get how many images downloaded out of total
            if progress_callback:
                progress_callback(i + 1, total_images)

        except Exception as e:
            print(f"❌ Failed to download image {i + 1} for {ad_id}: {e}")

    downloaded = 0

    for i, img_url in enumerate(img_urls):
        try:
            response = requests.get(img_url, timeout=10)
            response.raise_for_status()

            with open(folder / f"{i + 1:02}.jpg", "wb") as f:
                f.write(response.content)

            downloaded += 1

            if progress_callback:
                progress_callback(downloaded, total_images)

        except Exception as exc:
            print(f"❌ Failed to download image {i + 1} for {ad_id}: {exc}")

    driver.quit()

    print(f"✅ Downloaded {downloaded} images for {ad_id}")
    return downloaded


# %% CAZ
# -------


def check_caz(registration="FL56DPZ"):
    driver = create_stealth_driver(
        headless=True,
        url="https://multiple-vehiclecheck-pay.drive-clean-air-zone.service.gov.uk/what_would_you_like_to_do",
    )

    try:
        wait = WebDriverWait(driver, 15)
        driver.get(
            "https://multiple-vehiclecheck-pay.drive-clean-air-zone.service.gov.uk/what_would_you_like_to_do"
        )
        time.sleep(2)

        # Step 1: Choose "Check a vehicle" and Continue
        print("Page 1")
        try:
            # print('Finding "Check a vehicle" radio button...')
            check_vehicle_label = wait.until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//label[strong[text()='Check a vehicle']]")
                )
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
            wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "input[type='submit']"))
            ).click()
            # print('✔ Clicked "Continue".')
        except Exception as e:
            # print("❌ Could not find or click 'Continue' button")
            # with open("debug_page.html", "w", encoding="utf-8") as f:
            #     f.write(driver.page_source)
            raise e

        time.sleep(2)

        # Step 2: Enter registration number and select 'UK'
        print("Page 2")
        try:
            # print('Trying to enter registration...')
            wait.until(EC.presence_of_element_located((By.ID, "vrn"))).send_keys(
                registration
            )
            # print('✔ Registration entered. Trying to find "UK" radio button')
            driver.find_element(
                By.ID, "registration-country-1"
            ).click()  # UK is default
            # print('✔ "UK" radio button selected. Trying to find "Continue" button')
            driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
            # print('✔ "Continue" button clicked')
        except Exception as e:
            # print("❌ Could not enter reg, select 'UK' or click 'Continue' button")
            # with open("debug_page.html", "w", encoding="utf-8") as f:
            #     f.write(driver.page_source)
            raise e

        # Step 3: Confirm vehicle details
        print("Page 3")
        try:
            wait.until(EC.presence_of_element_located((By.ID, "confirm_details-1")))
            # print('Finding "Yes" radio button...')
            confirm_radio = driver.find_element(By.ID, "confirm_details-1")
            driver.execute_script("arguments[0].click();", confirm_radio)
            # print('✔ "Yes" confirmation selected. Finding "Confirm" button.')
            driver.find_element(By.CSS_SELECTOR, "input[type='submit']").click()
            # print('✔ "Confirm" button clicked.')
        except Exception as e:
            # print("❌ Could not confirm details")
            # with open("debug_page.html", "w", encoding="utf-8") as f:
            #     f.write(driver.page_source)
            raise e

        # Step 4: Scrape results table
        print("Page 4 (Final)")

        try:
            wait.until(EC.presence_of_element_located((By.ID, "compliance-table")))
            rows = driver.find_elements(By.CSS_SELECTOR, "#compliance-table tbody tr")

            results = []
            for row in rows:
                cols = row.find_elements(By.TAG_NAME, "td")
                results.append(
                    {
                        "Zone": cols[0].text.strip(),
                        "Daily Charge": cols[1].text.strip(),
                        "Zone Live": cols[2].text.strip(),
                        "Map URL": cols[3]
                        .find_element(By.TAG_NAME, "a")
                        .get_attribute("href"),
                        "Exemptions URL": cols[4]
                        .find_element(By.TAG_NAME, "a")
                        .get_attribute("href"),
                    }
                )
        except Exception as e:
            print("❌ Could not scrape results table")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            raise e

        return results

    finally:
        driver.quit()


if __name__ == "__main__":
    from database_utils import (
        check_ad_id_exists,
        get_saved_ad_ids,
        delete_ads_by_ad_id,
        delete_ads_by_search_id,
        load_ads,
    )
    from general_utils import extract_post_date
    from pprint import pprint

    pprint(check_caz())
