import os
import re
import sqlite3
import hashlib
from datetime import datetime

import pandas as pd
from pathlib import Path

# SQLite location
DATA_DIR = 'data'
DB_PATH = os.path.join(DATA_DIR, 'autotrader_listings.db')

# Create dir if doesn't exist
os.makedirs(DATA_DIR, exist_ok = True)

# Create SQLite table
def create_table_if_not_exists(table_name):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
                       CREATE TABLE IF NOT EXISTS {table_name} (
                           "Ad URL" TEXT,
                           "Ad ID" TEXT PRIMARY KEY,
                           "Title" TEXT,
                           "Subtitle" TEXT,
                           "Price" TEXT,
                           "Mileage" INTEGER,                           
                           "Registered Year" TEXT,
                           "Distance (miles)" INTEGER,
                           "Location" TEXT,
                           "Ad post date" TEXT,
                           "Favourited" INTEGER DEFAULT 0,
                           "Excluded" INTEGER DEFAULT 0,
                           "Scraped at" TEXT                           
                       )
                       ''')
        conn.commit()
        
def save_to_sql(data, table_name = 'ads'):
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.DataFrame(data)
        df.to_sql(table_name, conn, if_exists = 'append', index = False)        
        
def check_ad_id_exists(ad_id, table_name = 'ads'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT 1 FROM {table_name} WHERE \"Ad ID\" = ?", (ad_id,))
        return cursor.fetchone() is not None
        
def insert_test_ad(table_name='ads'):
    ad = {
        "Ad URL": "https://www.autotrader.co.uk/car-details/202507054201480",
        "Ad ID": "e46b69ca14",
        "Title": "Reliant Scimitar",
        "Subtitle": "3.0 GTE 2dr",
        "Price": "£4,500",
        "Mileage": 33543,
        "Registered Year": "1980 (W reg)",
        "Distance (miles)": 25,
        "Location": "Porthcawl",
        "Ad post date": "2025-07-05",
        "Favourited": 0,
        "Excluded": 0,
        "Scraped at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    save_to_sql([ad], table_name)
        
if __name__ == "__main__":
    create_table_if_not_exists('ads')
    insert_test_ad()
    # print(check_ad_id_exists('e46b69ca14'))
    pass