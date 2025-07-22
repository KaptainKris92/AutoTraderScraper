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
                           "Distance (miles)" INTEGER
                           "Location" TEXT,
                           "Ad posted date" TEXT,
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
        
if __name__ == "__main__":
    # create_table_if_not_exists('ads')
    pass