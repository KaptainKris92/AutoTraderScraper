import os
import sqlite3
import json
from datetime import datetime
import pandas as pd
from pathlib import Path


# SQLite location
DATA_DIR = Path('data')
DB_PATH = DATA_DIR / 'autotrader_listings.db'

# Create dir if doesn't exist
os.makedirs(DATA_DIR, exist_ok = True)

# Create SQLite table for storing scraped ad info
def create_ads_table(table_name = 'ads'):
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
        
def create_mot_history_table(table_name = 'mot_history'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
                       CREATE TABLE IF NOT EXISTS {table_name} (
                           "registration" TEXT PRIMARY KEY,
                           "mot_data" TEXT NOT NULL,
                           "ad_id" TEXT,
                           "created_at" TEXT NOT NULL                           
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
    
def update_flag(ad_id, column, value, table_name='ads'):
    if column not in ("Favourited", "Excluded"):
        raise ValueError("Invalid column")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'UPDATE {table_name} SET "{column}" = ? WHERE "Ad ID" = ?', (value, ad_id))
        conn.commit()

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
    
def load_ads(table = 'ads'):
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql_query(f'SELECT * FROM {table}', conn)
        df = df.fillna("").replace({float("nan"): ""})
        return df.to_dict(orient='records')
    
def get_saved_ad_ids(table_name = 'ads'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT `Ad ID`, `Ad URL` FROM {table_name}")
        return cursor.fetchall()
    
def save_mot_history(reg, data, ad_id = None, table_name = 'mot_history'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'''
            INSERT OR REPLACE INTO {table_name} (registration, mot_data, ad_id, created_at)
            VALUES (?, ?, ?, ?)
            ''',
            (reg.upper(), json.dumps(data), ad_id, datetime.now().isoformat())
        )
        conn.commit()

def get_mot_histories(ad_id = None, table_name = 'mot_history'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if ad_id is None: 
            cursor.execute(f"SELECT registration, mot_data, ad_id FROM {table_name}")            
        else:
            cursor.execute(f"SELECT registration, mot_data, ad_id FROM {table_name} WHERE ad_id = ?", (ad_id,))
        return [
            {"registration": row[0], "data": json.loads(row[1]), "ad_id": row[2]}
            for row in cursor.fetchall()
        ]
        
def delete_ads(ids_to_remove, table_name = 'ads'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            f'DELETE FROM {table_name} WHERE "Ad ID" = ?',
            [(ad_id,) for ad_id in ids_to_remove]
        )
        conn.commit()
                
def delete_mot_history(reg, table_name = 'mot_history'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE registration = ?", (reg.upper(),))
        conn.commit()
        
def bind_mot_to_ad(reg, ad_id, table_name = 'mot_history'):
    '''
    Returns: ad_id, ad_url
    '''
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if ad_id is None:
            cursor.execute(f"UPDATE {table_name} SET ad_id = NULL WHERE registration = ?", (reg.upper(),))
        else:
            cursor.execute(f"UPDATE {table_name} SET ad_id = ? WHERE registration = ?", (ad_id, reg.upper()))
        conn.commit()
        
def ensure_tables_exist():
    create_ads_table()
    create_mot_history_table()
        
if __name__ == "__main__":
    ensure_tables_exist()
    pass