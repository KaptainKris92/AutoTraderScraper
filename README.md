# AutoTraderScraper
Pulls listings according to a search criteria embedded in a link.

## Requirements
- ngrok
- Node.js
- React
- Tailwind CSS 

Set up ngrok account
**TODO: Add ability to enter ngrok credentials, then automatically configure ngrok for user**

## Set up

### ngrok

1. Create an ngrok account on https://ngrok.com/
2. Install ngrok by running `winget install ngrok -s msstore` in your terminal, or [downloading the installer](https://ngrok.com/download/).
3. Copy your authtoken from https://dashboard.ngrok.com/get-started/your-authtoken
4. Add your authtoken as an environment variable by running `$env:NGROK_AUTHTOKEN = "YOUR_AUTHTOKEN"`
Run `ngrok config add-authtoken $YOUR_AUTHTOKEN` from your terminal. 

### Python and Node.js packages
1. Set up a virtual environment by running `venv .venv` in the root repo (see [here](https://docs.python.org/3/library/venv.html) for details on `venv`). Alternatively, you may use other Python package managers such as `uv` ([link](https://docs.astral.sh/uv/)).
2. Activate the virtual environment by running `.venv/scripts/activate` from the root folder.
3. Install required Python packages by running `pip install -r requirements.txt` from the root repo folder.
4. Node.js packages can be installed by navigating to `react-app` folder, opening terminal, and running `npm install`

### MOT History

To use the MOT histroy feature, you must register for an MOT History API [here](https://documentation.history.mot.api.gov.uk/mot-history-api/register).    
After 1-5 working days, you should receive an e-mail with the variables below. You should store in a `AutoTraderScraper/.env` file:

- MOT_CLIENT_ID = "`Client ID`"
- MOT_CLIENT_SECRET = "`Client Secret`"
- MOT_API_KEY = "`API key`"
- SCOPE_URL = "`Scope URL`"
- TOKEN_URL = "`Token URL`"

## Scraping

From the repo root folder, run `py scraper.py` (or `python scraper.py` depending on your Python PATH configuration). This will update the database and thumbnail images by scraping AutoTrader. This may take a while. 

## UI

Run `py server.py` or `python server.py` from the repo root folder. This is needed for routing to the database via Flask.

In a separate terminal within the `react-app` folder, run `npm run dev:auto`. This will grant you access to the UI either through http://localhost:5173/, http://192.168.4.29:5173, or a randomly-generated ngrok link.

## License
This project is licensed under the [Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0)](https://creativecommons.org/licenses/by-nc/4.0/).

You may use, modify, and share this code for **non-commercial purposes only**, with proper attribution.  
**Commercial use is strictly prohibited without explicit permission.**

