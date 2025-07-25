import pandas as pd
import os, time
from datetime import datetime
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium_stealth import stealth

# Unique Advert IDs
import hashlib
import requests
from pathlib import Path

# Database functions
from utils.database_utils import create_ads_table, check_ad_id_exists, save_to_sql, get_saved_ad_ids, delete_ads, load_ads
from utils.general_utils import extract_post_date

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # Silence Tensorflow warnings: 0 = all logs, 1 = filter INFO, 2 = filter WARNING, 3 = filter ERROR

# With filters: Under £5k, within 50 miles of Caerphilly, Automatic transmission, <125k miles
# TODO: Make this modifiable
AUTOTRADER_URL = "https://www.autotrader.co.uk/car-search?maximum-mileage=125000&postcode=CF83%208TF&price-to=5000&radius=50&sort=relevance&transmission=Automatic"  

DATA_DIR = Path('data')
DEFAULT_MAX_SCROLLS = 1 # Maybe default should be all ads possible?
TABLE_NAME = 'ads'

def reject_cookies(driver, timeout=15):
    try:
        # Wait for iframe containing the cookie modal
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='consent']"))
        )
        iframe = driver.find_element(By.CSS_SELECTOR, "iframe[src*='consent']")
        driver.switch_to.frame(iframe)

        # Wait for the Reject All button inside the iframe
        WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Reject All')]"))
        )
        reject_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Reject All')]")
        driver.execute_script("arguments[0].click();", reject_button)
        print("✅ Clicked 'Reject All' cookie button inside iframe.")

        # Important: switch back to main content
        driver.switch_to.default_content()

    except Exception as e:
        print("⚠️ Failed to handle cookie popup:", e)
        
def create_stealth_driver(headless=True, url = AUTOTRADER_URL):
    options = Options()
    if headless:
        options.add_argument("--headless=new")  
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                         "AppleWebKit/537.36 (KHTML, like Gecko) "
                         "Chrome/114.0.0.0 Safari/537.36")
    # Suppress log warnings etc.
    options.add_argument("--log-level-3") # Suppresses all but fatal logs
    options.add_argument("--disable-logging")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

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

def scrape_autotrader(save_to_excel = True, max_scrolls = DEFAULT_MAX_SCROLLS):
    DATA_DIR.mkdir(parents=True, exist_ok=True)    
    driver = create_stealth_driver(headless = True, url = AUTOTRADER_URL)    
    reject_cookies(driver)
    time.sleep(3) # Give the page time to render listings

    # Wait until at least one car listing is loaded
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='advertCard']"))
        )
        print("Listings loaded.")
    except:
        print("Still couldn't find any listings.")
        print(driver.page_source[:2000])
        driver.quit()
        return

    # Scroll to bottom until no new content appears (stop at MAX_SCROLLS)
    scroll_pause_time = 1    
    last_height = driver.execute_script("return document.body.scrollHeight")

    for i in range(max_scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            print(f"🔄 Stopped scrolling at scroll #{i+1}, page fully loaded.")
            break
        last_height = new_height
    else:
        print("⚠️ Max scrolls reached, may still be incomplete.")

    car_data = []
    listings = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='advertCard']")
    print(f"🛻 Found {len(listings)} car listings after scrolling.")
    
    # Extract listings info
    for listing in listings: 
        try:
            title_elem = listing.find_element(By.CSS_SELECTOR, "a[data-testid='search-listing-title']")
            thumbnail_elem = listing.find_element(By.CSS_SELECTOR, "img.main-image")
            thumbnail_url = thumbnail_elem.get_attribute("src")
            href = title_elem.get_attribute("href")
            base_href = href.split("?")[0]  # Remove everything after '?'
            ad_url = "https://www.autotrader.co.uk" + base_href if base_href.startswith("/") else base_href
        except:
            ad_url = ""        
            thumbnail_url = None            
            
            
        # Generate stable ad_id
        ad_id = hashlib.md5(ad_url.encode('utf-8')).hexdigest()[:10] if ad_url else ""
        
        if check_ad_id_exists(ad_id, TABLE_NAME):
            print(f'Ad {ad_id} already scraped.') # REMOVE AFTER DEBUGGING
            continue        
        
        if thumbnail_url:
            download_thumbnail(ad_id, thumbnail_url)
            
        try:
            post_date = extract_post_date(ad_url)
        except:
            post_date = ""
        
        try:
            title = listing.find_element(By.CSS_SELECTOR, "[data-testid='search-listing-title']").text
        except:
            title = ""
                    
        try:
            price_elem = listing.find_element(By.CSS_SELECTOR, "div[class*='at__sc-u4ap7c-12'] span")
            price = price_elem.text.strip()
        except:
            price = ""

        try:
            subtitle = listing.find_element(By.CSS_SELECTOR, "[data-testid='search-listing-subtitle']").text
        except:
            subtitle = ""

        try:
            mileage = listing.find_element(By.CSS_SELECTOR, "[data-testid='mileage']").text
        except:
            mileage = ""
            
        # Convert mileage to numeric
        mileage_numeric = ""
        if mileage:
            try:
                mileage_numeric = int(mileage.lower().replace("miles", "").replace(",", "").strip())
            except:
                pass

        try:
            reg_year = listing.find_element(By.CSS_SELECTOR, "[data-testid='registered_year']").text
        except:
            reg_year = ""

        try:
            location = listing.find_element(By.CSS_SELECTOR, "[data-testid='search-listing-location']").text
        except:
            location = ""
            
        loc_match = re.match(r"(.+?)\s*\((\d+)\s*miles\)", location)
        if loc_match:
            city, dist = loc_match.groups()
            try:
                dist = int(dist)
            except ValueError:
                dist = None
        else:
            city, dist = None, None
            
        # Remove subtitle and price from title if present
        cleaned_title = title
        if subtitle and subtitle in cleaned_title:
            cleaned_title = cleaned_title.replace(subtitle, "")
        if price and price in cleaned_title:
            cleaned_title = cleaned_title.replace(price, "")
        cleaned_title = cleaned_title.strip()
        # Remove trailing newline and comma if present
        cleaned_title = re.sub(r'[\n\r]+,?$', '', cleaned_title).strip()

        car_data.append({
            'Ad URL': ad_url,
            'Ad ID': ad_id,
            'Title': cleaned_title,
            'Subtitle': subtitle,
            'Price': price,
            'Mileage': mileage_numeric,
            'Registered Year': reg_year,
            'Distance (miles)': dist,
            'Location': city,
            'Ad post date': post_date,
            'Favourited': 0,
            'Excluded': 0,
            'Scraped at': datetime.now().strftime("%Y-%m-%d %H:%M:%S")                                
        })
        
        if not title:
            print("⚠️ Skipped listing with missing title or fields.")
            
    driver.quit()

    df = pd.DataFrame(car_data)
    df = df.drop_duplicates(subset = 'Ad ID')
    
    # Remove any ads no longer listed
    live_ad_ids = set(df['Ad ID'])
    saved_ads = load_ads(TABLE_NAME)
    saved_ad_ids = set(ad['Ad ID'] for ad in saved_ads)
    to_remove = saved_ad_ids - live_ad_ids
    
    if to_remove:
        print(f'🗑️ Removing {len(to_remove)} ads no longer listed.')
        delete_ads(to_remove, TABLE_NAME)

        # Remove associated thumbnail and image folders
        for ad_id in to_remove:
            thumb_path = Path("thumbnails") / f"{ad_id}.jpg"
            image_folder = Path("images") / ad_id

            if thumb_path.exists():
                try:
                    thumb_path.unlink()
                    print(f"🗑️ Deleted thumbnail for {ad_id}")
                except Exception as e:
                    print(f"⚠️ Could not delete thumbnail for {ad_id}: {e}")

            if image_folder.exists():
                try:
                    for file in image_folder.glob("*"):
                        file.unlink()
                    image_folder.rmdir()
                    print(f"🗑️ Deleted image folder for {ad_id}")
                except Exception as e:
                    print(f"⚠️ Could not delete image folder for {ad_id}: {e}")

    
    if save_to_excel:
        file_path = DATA_DIR / f"cars_{datetime.now().date()}.xlsx"
        df.to_excel(file_path, index=False)
        print(f"Saved {len(df)} listings to {file_path}")
    return df

def download_thumbnail(ad_id, thumbnail_url, save_dir = 'thumbnails'):
    Path(save_dir).mkdir(parents = True, exist_ok = True)
    try:
        response = requests.get(thumbnail_url, timeout = 10)
        if response.status_code == 200:
            with open(f'{save_dir}/{ad_id}.jpg', 'wb') as f:
                f.write(response.content)
            print(f'✅ Saved thumbnail for {ad_id}')
        else:
            print(f'❌ Failed to download image for {ad_id}, status {response.status_code}')     
    except Exception as e:
        print(f"❌ Error downloading thumbnail for {ad_id}: {e}")
        
def download_missing_images(limit = None):
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

def download_pictures(ad_id, ad_url):
    folder = Path("images") / ad_id
    folder.mkdir(parents=True, exist_ok=True)
    driver = create_stealth_driver(headless = True, url = ad_url)
    reject_cookies(driver)

    try:        
        time.sleep(1)

        # Click a thumbnail on ad page instead of the 'View gallery' button
        try:
            thumb = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "button[data-testid^='open-carousel']"))
            )
            driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", thumb)
            time.sleep(0.5)
            thumb.click()
            print(f"✅ Clicked thumbnail to open gallery for {ad_id}")
        except Exception as e:
            print(f"⚠️ Failed to click thumbnail for {ad_id}: {e}")
            driver.quit()
            return

        # Wait for modal to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog'] img"))
        )
        
        time.sleep(1)  # Ensure images fully render

    except Exception as e:
        print(f"⚠️ Could not open gallery for {ad_id}: {e}")
        driver.quit()
        return

    # ✅ Extract images
    try:
        image_elements = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'] picture source")
        
        srcset_urls = []
        for elem in image_elements:
            srcset = elem.get_attribute('srcset')     
            if srcset:
                urls = [s.strip().split(" ")[0] for s in srcset.split(",") if "media" in s]
                srcset_urls.extend(urls)
                
        img_urls = extract_highest_res_images(srcset_urls)

        if not img_urls:
            print("⚠️ No modal image URLs found, falling back to thumbnails.")
            thumb_elements = driver.find_elements(By.CSS_SELECTOR, "img.ImageGalleryImage__image")
            img_urls = list({
                img.get_attribute("src")
                for img in thumb_elements
                if img.get_attribute("src") and "media" in img.get_attribute("src")
            })

    except Exception as e:
        print(f"⚠️ Could not extract image URLs for {ad_id}: {e}")
        img_urls = []

    # ✅ Download images
    for i, img_url in enumerate(img_urls):
        try:
            img_data = requests.get(img_url, timeout=10).content
            with open(folder / f"{i+1:02}.jpg", "wb") as f:
                f.write(img_data)
        except Exception as e:
            print(f"❌ Failed to download image {i+1} for {ad_id}: {e}")

    driver.quit()
    print(f"✅ Downloaded {len(img_urls)} images for {ad_id}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--scrape", action="store_true", help="Scrape new ads from AutoTrader")
    parser.add_argument("--download", action="store_true", help="Download images for saved ads")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of missing images to download (generally just used for debugging)")
    parser.add_argument("--max-scrolls", type=int, default = DEFAULT_MAX_SCROLLS, help = "How many times to scroll during scraping. (Alternatively, use `--scroll-until-end`)")
    parser.add_argument("--scroll-until-end", action="store_true", help="Keep scrolling until all ads are loaded.")
    
    args = parser.parse_args()

    if args.scrape:
        create_ads_table()
        max_scrolls = 9999 if args.scroll_until_end else args.max_scrolls # 9999 should be sufficient.
        df = scrape_autotrader(max_scrolls = args.max_scrolls)
        save_to_sql(df, TABLE_NAME)
    if args.download:
        download_missing_images(limit=args.limit)    
            
    
