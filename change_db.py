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
    execute_query("DELETE FROM ads")
    print("Deleted all listings")    
    
def clear_exclude(timeframe):
    if timeframe == 'all':
        query = '''
        UPDATE ads
        SET Excluded = 0
        '''
        execute_query(query)
        
    elif timeframe == 'today':
        today_str = datetime.now().strftime('%Y-%m-%d')
        query = f'''
        UPDATE ads
        SET Excluded = 0
        WHERE [Scraped at] LIKE "{today_str}%"
        '''
        execute_query(query)
    else:
        print("Invalid timeframe.")
    

def clear_favourite(timeframe):
    if timeframe == 'all':
        query = '''
        UPDATE ads
        SET Favourited = 0
        '''
        execute_query(query)
    elif timeframe == 'today':
        today_str = datetime.now().strftime('%Y-%m-%d')
        query = f'''
        UPDATE ads
        SET Excluded = 0
        WHERE [Scraped at] LIKE "{today_str}%"
        '''
        execute_query(query)
    else:
        print("Invalid timeframe.")
    pass

if __name__ == "__main__":
    ans = None
    while ans not in ['clear all', 'clear today', 'reset exclude all', 'reset exclude today', 'reset favourite all']:
        ans = input("Which ads to delete? 'clear', 'reset exclude', or 'reset favourite'? 'all' or 'today'? Command must be e.g.: `reset favourite today`")
    if ans == 'clear all':
        clear_all()
    elif ans == 'clear today':
        clear_today()
    elif ans == 'reset exclude all':
        clear_exclude('all')
    elif ans == 'reset exclude today':
        clear_exclude('today')
    elif ans == 'reset favourite all':
        clear_favourite('all')
    elif ans == 'reset favourite today':
        clear_favourite('today')
