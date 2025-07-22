from bs4 import BeautifulSoup
from urllib.parse import urljoin
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

# OCR of license plate
import easyocr

# Database functions
from utils.database_utils import create_table_if_not_exists, check_ad_id_exists, save_to_sql
from utils.general_utils import extract_post_date

from dotenv import load_dotenv
load_dotenv('./.env')


# With filters: Under £5k, within 50 miles of Caerphilly, Automatic transmission, <125k miles
AUTOTRADER_URL = "https://www.autotrader.co.uk/car-search?maximum-mileage=125000&postcode=CF83%208TF&price-to=5000&radius=50&sort=relevance&transmission=Automatic"  

DATA_DIR = "data"
MAX_SCROLLS = 1 
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
        
def create_stealth_driver(headless=True):
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
    
    return driver

def scrape_autotrader(save_to_excel = True):
    os.makedirs(DATA_DIR, exist_ok=True)
    driver = create_stealth_driver(headless = True)    
    driver.get(AUTOTRADER_URL)

    reject_cookies(driver)
    
    time.sleep(5) # Give the page time to render listings

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
    scroll_pause_time = 2    
    last_height = driver.execute_script("return document.body.scrollHeight")

    for i in range(MAX_SCROLLS):
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
            href = title_elem.get_attribute("href")
            base_href = href.split("?")[0]  # Remove everything after '?'
            ad_url = "https://www.autotrader.co.uk" + base_href if base_href.startswith("/") else base_href
        except:
            ad_url = ""        
            
            
        # Generate stable ad_id
        ad_id = hashlib.md5(ad_url.encode('utf-8')).hexdigest()[:10] if ad_url else ""
        
        if check_ad_id_exists(ad_id, TABLE_NAME):
            print(f'Ad {ad_id} already scraped.') # REMOVE AFTER DEBUGGING
            continue        
            
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

        car_data.append({
            'Ad URL': ad_url,
            'Ad ID': ad_id,
            'Title': title,
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
    
    if save_to_excel:
        file_path = os.path.join(DATA_DIR, f"cars_{datetime.now().date()}.xlsx")
        df.to_excel(file_path, index=False)
        print(f"Saved {len(df)} listings to {file_path}")
    return df


def download_pictures(ad_id, ad_url):
    folder = Path("images") / ad_id
    folder.mkdir(parents=True, exist_ok=True)

    driver = create_stealth_driver(headless = True)
    driver.get(ad_url)
    reject_cookies(driver)

    try:        
        time.sleep(2)

        # ✅ Click a thumbnail instead of the 'View gallery' button
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
        
        time.sleep(2)  # Ensure images fully render

    except Exception as e:
        print(f"⚠️ Could not open gallery for {ad_id}: {e}")
        driver.quit()
        return

    # ✅ Extract images
    try:
        image_elements = driver.find_elements(By.CSS_SELECTOR, "div[role='dialog'] picture source")

        img_urls = list({
            elem.get_attribute("srcset") or elem.get_attribute("src")
            for elem in image_elements
            if (elem.get_attribute("srcset") or elem.get_attribute("src")) and "media" in (elem.get_attribute("srcset") or elem.get_attribute("src"))
        })

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


if __name__ == "__main__":
    scraped_df = scrape_autotrader()
    create_table_if_not_exists(TABLE_NAME)
    save_to_sql(scraped_df, TABLE_NAME)
    print(f'{len(scraped_df)} new listings saved to database')
    
    # plate_sets = []
    # for _, row in scraped_df.iterrows():
    #     ad_id = row['Ad ID']
    #     ad_url = row['Ad URL']
    #     download_pictures(ad_id, ad_url)
    #     folder = f'images/{ad_id}'
    #     reader = easyocr.Reader(['en'], gpu=True)
    #     all_texts = []
    #     for filename in os.listdir(folder):
    #         if filename.lower().endswith((".jpg", ".jpeg", ".png")):
    #             img_path = os.path.join(folder, filename)
    #             try:
    #                 results = reader.readtext(img_path, detail=0, paragraph=False)
    #                 all_texts.extend(results)
    #             except Exception as e:
    #                 print(f"Failed to process {filename}: {e}")
    #     plate_set = clean_and_match_plates(all_texts)
    #     plate_sets.append(', '.join(plate_set) if plate_set else "")

    # scraped_df['Possible Plates'] = plate_sets
    # scraped_df.to_excel(os.path.join(DATA_DIR, f"cars_with_plates_{datetime.now().date()}.xlsx"), index=False)
    
    
