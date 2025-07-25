import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

MOT_CLIENT_ID = os.getenv('MOT_CLIENT_ID')
MOT_CLIENT_SECRET = os.getenv('MOT_CLIENT_SECRET')
MOT_API_KEY = os.getenv('MOT_API_KEY')
TOKEN_URL = os.getenv('TOKEN_URL')
SCOPE_URL = os.getenv('SCOPE_URL')

BASE_URL = 'https://history.mot.api.gov.uk/v1/trade/vehicles/registration/'

# Cache the token (they expire every 60 minutes)
_token_cache = {
    'access_token': None,
    'expires_at': 0
}

def get_access_token():
    ''' Fetches and caches the access token if expires. '''
    now = time.time()
    if _token_cache['access_token'] and _token_cache['expires_at'] > now + 60:
        return _token_cache['access_token']
    
    print('🔄 Fetching new MOT API token...')
    data = {
        'grant_type': 'client_credentials',
        'client_id': MOT_CLIENT_ID,
        'client_secret': MOT_CLIENT_SECRET,
        'scope': SCOPE_URL
    }
    
    try:
        response = requests.post(TOKEN_URL, data = data)
        response.raise_for_status()
        token_data = response.json()
        _token_cache['access_token'] = token_data['access_token']
        _token_cache['expires_at'] = now + int(token_data.get('expires_in', 3600)) 
        return _token_cache['access_token']
    except Exception as e:
        print('❌ Error retrieving access token:', e)
        return None

def get_mot_history(reg):
    token = get_access_token()
    
    if not token:
        return {'error': 'Unable to authenticate'}
    
    headers = {
        'Accept': 'application/json+v6',
        'x-api-key': MOT_API_KEY,
        'Authorization': f'Bearer {token}',       
    }
    
    try:        
        response = requests.get(f'{BASE_URL}{reg}', headers = headers)
        if response.status_code == 200:
            return response.json()
        else:
            return {'error': f'API error {response.status_code}', 'details': response.text}
    except Exception as e:
        return {'error': str(e)}
    