import os
import sqlite3
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
DB_PATH = Path(os.getenv("SQLITE_PATH", DATA_DIR / "autotrader_listings.db"))
os.makedirs(DATA_DIR, exist_ok=True)

# %% Create tables
# ----------------

# Scraped ad information


def create_ads_table(table_name='ads'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        # TODO: Remove whitespaces and capitalisation from these columns (CHANGE ALL ASSOCIATED REFERENCES)
        cursor.execute(f'''
                       CREATE TABLE IF NOT EXISTS {table_name} (
                           "ad_url" TEXT,
                           "ad_id" TEXT PRIMARY KEY,
                           "title" TEXT,
                           "subtitle" TEXT,
                           "price" TEXT,
                           "mileage" INTEGER,
                           "reg_year" TEXT,
                           "distance" INTEGER,
                           "location" TEXT,
                           "post_date" TEXT,
                           "favourited" INTEGER DEFAULT 0,
                           "favourited_date" TEXT,
                           "excluded" INTEGER DEFAULT 0,
                           "excluded_date" TEXT,
                           "scrape_date" TEXT,
                           "search_id" INTEGER
                       )
                       ''')
        conn.commit()

# Results from MOT History API


def create_mot_history_table(table_name='mot_history'):
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

# Results from CAZ website


def create_caz_table(table_name='caz'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                registration TEXT,
                zone TEXT,
                daily_charge TEXT,
                zone_live TEXT,
                map_url TEXT,
                exemptions_url TEXT,
                created_at TEXT
            )
        ''')
        conn.commit()

# Search parameter profiles


def create_search_profiles_table():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
                    CREATE TABLE IF NOT EXISTS search_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        params TEXT NOT NULL,
                        generated_url TEXT,
                        last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                    ''')

# %% Save to tables
# ------------------

# Scraped ad data


def save_ads_data(data, table_name='ads'):
    import pandas as pd
    df = pd.DataFrame(data)

    if df.empty:
        print("⚠️ DataFrame is empty — skipping save.")
        return

    if 'ad_id' not in df.columns:
        print("⚠️ DataFrame has no 'ad_id' column — skipping save.")
        return

    with sqlite3.connect(DB_PATH) as conn:
        existing_ids = pd.read_sql(f'SELECT ad_id FROM {table_name}', conn)[
            'ad_id'].tolist()
        df = df[~df['ad_id'].isin(existing_ids)]  # Drops duplicate IDs
        df.to_sql(table_name, conn, if_exists='append', index=False)

# CAZ website results table


def save_caz_data(registration, caz_data, table_name='caz'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()

        # Delete existing data for the registration to avoid duplicates
        cursor.execute(
            f"DELETE FROM {table_name} WHERE registration = ?", (registration.upper(),))

        for entry in caz_data:
            cursor.execute(f'''
                INSERT INTO {table_name}
                (registration, zone, daily_charge, zone_live,
                 map_url, exemptions_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                registration.upper(),
                entry.get('Zone'),
                entry.get('Daily Charge'),
                entry.get('Zone Live'),
                entry.get('Map URL'),
                entry.get('Exemptions URL'),
                timestamp
            ))
        conn.commit()


def save_mot_history(reg, data, ad_id=None, table_name='mot_history'):
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

# Saves user search settings into a profile


def save_search_params(name, params, generated_url=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO search_profiles (name, params, generated_url, last_updated) VALUES (?, ?, ?, ?)",
            (name, json.dumps(params, sort_keys=True),
             generated_url, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid

# Update the last_updated field whenever a table is refreshed


def update_search_profile_timestamp(search_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(f"""
            UPDATE search_profiles
            SET last_updated = ?
            WHERE id = ?
        """, (datetime.now().isoformat(), search_id,))


# %% Retrieve data from tables
# ------------------------------

def load_ads(table='ads', search_id=None):
    import pandas as pd
    with sqlite3.connect(DB_PATH) as conn:
        if search_id is None:
            query = f'SELECT * FROM {table}'
        else:
            query = f'SELECT * FROM {table} WHERE search_id = {search_id}'

        df = pd.read_sql_query(
            query, conn)
        df = df.fillna("").replace({float("nan"): ""})
        return df.to_dict(orient='records')


def get_saved_ad_ids(table_name='ads'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT `ad_id`, `ad_url` FROM {table_name}")
        return cursor.fetchall()


def get_mot_histories(ad_id=None, table_name='mot_history'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if ad_id is None:
            cursor.execute(
                f"SELECT registration, mot_data, ad_id FROM {table_name}")
        else:
            cursor.execute(
                f"SELECT registration, mot_data, ad_id FROM {table_name} WHERE ad_id = ?", (ad_id,))
        return [
            {"registration": row[0], "data": json.loads(
                row[1]), "ad_id": row[2]}
            for row in cursor.fetchall()
        ]


def get_caz_data(registration, table_name="caz"):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT zone, daily_charge, zone_live, map_url, exemptions_url FROM {table_name} WHERE registration = ?",
            (registration.upper(),),
        )
        rows = cursor.fetchall()
        return [
            {
                "Zone": row[0],
                "Daily Charge": row[1],
                "Zone Live": row[2],
                "Map URL": row[3],
                "Exemptions URL": row[4],
            }
            for row in rows
        ]


def get_search_profiles(profile_id=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        if profile_id is not None:
            cursor.execute(
                """
                SELECT 	sp.id, 
                        sp.name, 
                        sp.params, 
                        sp.generated_url, 
                        sp.last_updated, 
                        COUNT(a.search_id) AS ad_count 
                FROM search_profiles AS sp
                LEFT JOIN ads a ON a.search_id = sp.id 
                WHERE id = ?
                GROUP BY sp.id 
                ORDER BY sp.last_updated DESC;
                """,
                (profile_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "id": row[0],
                "name": row[1],
                "params": json.loads(row[2]),
                "url": row[3],
                "last_updated": row[4],
                "ad_count": row[5]
            }
        else:
            cursor.execute(
                """
                SELECT 	sp.id, 
                        sp.name, 
                        sp.params, 
                        sp.generated_url, 
                        sp.last_updated, 
                        COUNT(a.search_id) AS ad_count 
                FROM search_profiles AS sp
                LEFT JOIN ads a ON a.search_id = sp.id 
                GROUP BY sp.id 
                ORDER BY sp.last_updated DESC;
                """
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row[0],
                    "name": row[1],
                    "params": json.loads(row[2]),
                    "url": row[3],
                    "last_updated": row[4],
                    "ad_count": row[5]
                }
                for row in rows
            ]


# Checks if search parameter combo already in database
def search_profile_exists(params):
    params_json = json.dumps(params, sort_keys=True)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name from search_profiles WHERE params = ?",
            (params_json,)
        )
        row = cursor.fetchone()
        return row[0] if row else None

# %% Delete rows from tables
# ---------------------------


def delete_ads_by_ad_id(ids_to_remove, table_name='ads'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.executemany(
            f'DELETE FROM {table_name} WHERE "ad_id" = ?',
            [(ad_id,) for ad_id in ids_to_remove]
        )
        conn.commit()


def delete_ads_by_search_id(search_id, table_name='ads'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'DELETE FROM {table_name} WHERE search_id = ?',
            (search_id,)
        )
        conn.commit()


def delete_mot_history(reg, table_name='mot_history'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"DELETE FROM {table_name} WHERE registration = ?", (reg.upper(),))
        conn.commit()


def delete_profile(profile_id):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM search_profiles WHERE id = ?", (profile_id,))
        conn.commit()

# %% Other utils
# --------------


def check_ad_id_exists(ad_id, table_name='ads'):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"SELECT 1 FROM {table_name} WHERE ad_id = ?", (ad_id,))
        return cursor.fetchone() is not None

# (Un-)favourite/(Un-)exclude ads


def update_flag(ad_id, column, value, table_name='ads'):
    if column not in ("favourited", "excluded"):
        raise ValueError("Invalid column")
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f'UPDATE {table_name} SET "{column}" = ? WHERE "ad_id" = ?', (value, ad_id))
        conn.commit()

# Link MOT History to an ad_id


def bind_mot_to_ad(reg, ad_id, table_name='mot_history'):
    '''
    Returns: ad_id, ad_url
    '''
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        if ad_id is None:
            cursor.execute(
                f"UPDATE {table_name} SET ad_id = NULL WHERE registration = ?", (reg.upper(),))
        else:
            cursor.execute(
                f"UPDATE {table_name} SET ad_id = ? WHERE registration = ?", (ad_id, reg.upper()))
        conn.commit()

# Create all tables if don't exist


def ensure_tables_exist():
    create_ads_table()
    create_mot_history_table()
    create_caz_table()
    create_search_profiles_table()


if __name__ == "__main__":
    ensure_tables_exist()
    pass
