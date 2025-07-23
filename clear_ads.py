# USED FOR DEBUGGING

import sqlite3
from datetime import datetime

DB_PATH = 'data/autotrader_listings.db'

def execute_query(query):
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query)
    conn.commit()
    conn.close()
    print('Query executed.')
    
    

def clear_today():
    # Today's date in YYYY-MM-DD format
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    query = f'''
    DELETE FROM ads
    WHERE [Scraped at] LIKE "{today_str}%"
    '''
    
    execute_query(query)
    print(f"Deleted all listings scraped on {today_str}.")
    
def clear_all():
    execute_query("DELETE * FROM ads")
    print("Deleted all listings")    

if __name__ == "__main__":
    ans = None
    while ans not in ['all', 'today']:
        ans = input("Which ads to delete? 'all' or 'today'? ")
    if ans == 'all':
        clear_all()
    elif ans == 'today':
        clear_today()
