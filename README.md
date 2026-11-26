# Virtual Rain Gauge (Web PWA)

Installable Progressive Web App port of the mobile Virtual Rain Gauge.

## Features

- Satellite map with Last week / Growing Season / Crop Year precipitation overlays
- Tap the map for point precipitation values
- Daily and season comparison charts
- Dynamic legend from the API
- Instructions / credits
- Soft update banner when a newer app version is required
- Installable on Android Chrome (Add to Home screen / Install app)

## Develop

```bash
npm install
npm run dev
```

Open http://localhost:5173

## Build

```bash
npm run build
npm run preview
```

Output is in `dist/`.

## API

The app calls the Rain Gauge API at `VITE_API_BASE_URL` (build time; `src/config/apiConfig.js`
has the original hosted API as the default). `server/` is a FastAPI implementation of the same
endpoints that reads daily HRDPA rasters on the server and also provides the map overlays through
TiTiler; the web app draws overlays from the `tiles` field of `legend_info`, which only that server
returns.

## Deploy

See `deploy/README.md` (nginx + Docker on a Linux server).

The Vercel / Cloud Run instructions were removed because that hosting no longer serves the
overlays.

**Do not use Firebase for this app**: the older portal lives in `raingauge-app.web.app`.

## Install on Android

1. Open the **HTTPS** site in Chrome.
2. Menu → **Install app** or **Add to Home screen**.
3. Launch from the home screen for a fullscreen (standalone) experience.

HTTPS is required for install prompts.

## Version

App version is in `src/config/version.js` and `package.json`. Keep them in sync when releasing.
