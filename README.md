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

In a separate terminal within the `react-app` folder, run `npm run dev:auto`. This will grant you access to the UI either through http://localhost:5173/, http://1992.168.4.29:5173, or a random ngrok link.
