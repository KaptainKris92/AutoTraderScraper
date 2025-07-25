# AutoTraderScraper
Pulls listings according to a search criteria embedded in a link.

## Requirements
- ngrok
- Node.js
- React
- Tailwind CSS 

Python packages can be installed by running `pip install -r requirements.txt`
Node.js packages can be installed by navigating to `react-app` folder, opening terminal, and running `npm install`

## Scraping

Run `py scraper.py`. This will update the database and thumbnail images by scraping AutoTrader. This may take a while. 

## UI

Run `py server.py`. This is needed for routing to the database via Flask.

In a separate terminal within the `react-app` folder, run `npm run dev:auto`. This will grant you access to the UI either through http://localhost:5173/, http://192.168.4.29:5173, or a randomly-generated ngrok link.

## MOT History

Register for an MOT History API (here)[https://documentation.history.mot.api.gov.uk/mot-history-api/register].    
After 1-5 working days, you should receive an e-mail with the variables below. You should store in a `AutoTraderScraper/.env` file:

- MOT_CLIENT_ID = "<Client ID>"
- MOT_CLIENT_SECRET = "<Client Secret>"
- MOT_API_KEY = "<API key>"
- SCOPE_URL = "<Scope URL>"
- TOKEN_URL = "<Token URL>"
