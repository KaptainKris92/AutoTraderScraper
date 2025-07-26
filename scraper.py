
from pathlib import Path
from utils.scrape_utils import scrape_autotrader, download_missing_images
from utils.database_utils import create_ads_table, save_to_sql

DATA_DIR = Path('data')
DEFAULT_MAX_SCROLLS = 1 # Maybe default should be all ads possible?
TABLE_NAME = 'ads'

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
        max_scrolls = 999999 if args.scroll_until_end else args.max_scrolls 
        df = scrape_autotrader(max_scrolls = max_scrolls)
        save_to_sql(df, TABLE_NAME)
    if args.download:
        download_missing_images(limit=args.limit)    
            
    
