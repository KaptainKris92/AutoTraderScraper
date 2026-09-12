# AutoTraderScraper

A local web application for creating AutoTrader search profiles, scraping matching vehicle listings, and reviewing the results.

The application uses a Python/Flask backend, a React/Vite frontend, Selenium for AutoTrader scraping, and SQLite for local storage.

## Requirements

* Python 3
* Node.js 20.19+ or 22.12+
* Google Chrome
* An ngrok account and authtoken if you want to access the application through a public ngrok URL

React, Vite, Tailwind CSS, and the ngrok JavaScript SDK are installed automatically through npm and do not need to be installed separately.

## First-time setup

Clone the repository and open a terminal in the repository root.

### Python

Create a virtual environment:

```powershell
python -m venv .venv
```

Activate it in PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the Python dependencies:

```powershell
python -m pip install -r requirements.txt
```

If PowerShell prevents `Activate.ps1` from running because scripts are disabled, either use Command Prompt to activate the environment or change the PowerShell execution policy for your user account.

### Node.js

Navigate to the React application:

```powershell
cd react-app
```

Install the exact dependency versions recorded in `package-lock.json`:

```powershell
npm ci
```

Return to the repository root:

```powershell
cd ..
```

## Environment variables

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

The `.env` file is excluded from Git and must not be committed.

### ngrok

ngrok is optional when running the application locally.

To enable the public ngrok URL:

1. Create an ngrok account.
2. Copy your ngrok authtoken from your ngrok dashboard.
3. Add it to the repository-root `.env` file:

```env
NGROK_AUTHTOKEN=your_ngrok_authtoken
```

A separate installation of the ngrok command-line application is not required. The project uses the `@ngrok/ngrok` Node.js SDK.

## Running the application

The backend and frontend run in separate terminals.

### Terminal 1 — Flask backend

From the repository root, activate your Python virtual environment and run:

```powershell
python server.py
```

The backend runs on port 5000.

### Terminal 2 — React frontend

Navigate to:

```powershell
cd react-app
```

For local development:

```powershell
npm run dev
```

Then open:

```text
http://localhost:5173
```

To start the frontend and create a public ngrok tunnel:

```powershell
npm run dev:auto
```

The terminal will display the generated ngrok URL.

## Using the application

1. Open **Settings**.
2. Enter your AutoTrader search criteria and save a search profile.
3. Find the saved profile and click **Update Table**.
4. Wait for the scraper to complete.
5. Open **Home** to review the scraped adverts.

The **Update Table** button calls the Flask backend, which launches the AutoTrader scraper in the background, downloads missing thumbnails, and updates the local database automatically.

Running **Update Table** again refreshes the selected search profile and removes adverts that are no longer present in the AutoTrader results.

Application data is stored locally in:

```text
data/autotrader_listings.db
```

Downloaded thumbnails and gallery images are stored in:

```text
thumbnails/
images/
```

If scraping fails before listing cards can be found, a diagnostic browser screenshot is stored in:

```text
screenshots/
```

## MOT History

MOT History integration is optional.

To use it, register for access to the MOT History API. Once your credentials have been issued, add them to the repository-root `.env` file:

```env
MOT_CLIENT_ID=your_client_id
MOT_CLIENT_SECRET=your_client_secret
MOT_API_KEY=your_api_key
SCOPE_URL=your_scope_url
TOKEN_URL=your_token_url
```

Restart the Flask backend after changing `.env`.

## Troubleshooting

If **Update Table** returns no adverts, check the scraping progress modal and the Flask terminal. Scraper failures are reported in both places.

If AutoTrader's page structure changes, the scraper's `data-testid` selectors may need to be updated.

If `npm run dev:auto` reports that `NGROK_AUTHTOKEN` is missing, check that `.env` exists in the repository root rather than inside `react-app`.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).

You may use, modify, and share this code for non-commercial purposes with proper attribution.

Commercial use is prohibited without explicit permission.
