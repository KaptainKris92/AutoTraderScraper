from bs4 import BeautifulSoup
from urllib.parse import urljoin
from PIL import Image
import pandas as pd
import os, time
from datetime import datetime
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait


# With filters: Under £5k, within 50 miles of Caerphilly, Automatic transmission, <125k miles
AUTOTRADER_URL = "https://www.autotrader.co.uk/car-search?maximum-mileage=125000&postcode=CF83%208TF&price-to=5000&radius=50&sort=relevance&transmission=Automatic"  
SAVE_DIR = "car_data"
MAX_SCROLLS = 50 

# Doesn't work yet. May be unnecessary
def accept_cookies(driver, timeout=15):
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





def scrape_autotrader():
    os.makedirs(SAVE_DIR, exist_ok=True)

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36")


    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(AUTOTRADER_URL)

    # Wait for and accept cookies (if present)
    accept_cookies(driver)
    # Give the page time to render listings
    time.sleep(5)  # Optional: add delay before checking for listings

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

    # Scroll to bottom until no new content appears (max 15 scrolls)
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
    for listing in listings:
        try:
            title = listing.find_element(By.CSS_SELECTOR, "[data-testid='search-listing-title']").text
        except:
            title = ""
            
        # Extract price
        price_match = re.search(r"£[\d;]+", title)
        if price_match:
            price = price_match.group()
            title = title.replace(f", {price}", "").strip()
        else:
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
            
        loc_match = re.match(r"(.+?)\s*\(([\d,]+ miles)\)", location)
        if loc_match:
            city, dist = loc_match.groups()
            location_reformatted = f'{dist} ({city})'
        else:
            location_reformatted = location

        car_data.append({
            "Title": title,
            "Subtitle": subtitle,
            "Price": price,
            "Mileage": mileage,
            "Mileage (numeric)": mileage_numeric,
            "Registered Year": reg_year,
            "Location": location_reformatted
        })
        if not title:
            print("⚠️ Skipped listing with missing title or fields.")
            
    driver.quit()

    df = pd.DataFrame(car_data)
    file_path = os.path.join(SAVE_DIR, f"cars_{datetime.now().date()}.xlsx")
    df.to_excel(file_path, index=False)
    print(f"Saved {len(df)} listings to {file_path}")


if __name__ == "__main__":
    scrape_autotrader()
