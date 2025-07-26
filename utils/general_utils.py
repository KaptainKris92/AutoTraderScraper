import re
from datetime import datetime

def extract_post_date(ad_url):
    match = re.search(r'/car-details/(\d{8})', ad_url)
    if match:
        return datetime.strptime(match.group(1), '%Y%m%d').date()
    return None                              