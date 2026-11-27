# Virtual Rain Gauge: API and tiles from the VM's own rasters

Date: 2026-11-26. Status: implemented 2026-11-26.

## Goal

The web app stops depending on Google Cloud. The six API endpoints it calls and the three rain
overlays it draws are served from the GAIG VM, computed from the rasters the VM's own HRDPA
pipeline already produces (the VM's rain directory, `DEPLOY_RAIN_DIR` in `deploy/.env`). The API
keeps the request and response formats of the current Cloud Run API (`api.realfield.ca`), so the
mobile app could be pointed at it later without changes to its code.

Out of scope: the mobile app, Nam's domains, shutting down the Google resources, a host name for
the VM (the bare-IP Let's Encrypt certificate stays).

## Architecture

```
browser ── /raingauge/            nginx ── static build (unchanged)
        ── /raingauge/api/...     nginx ── raingauge-api container (127.0.0.1:<port>)   [new]
        ── /raingauge/tiles/...   nginx ── TiTiler container (127.0.0.1:8000)          [new route]
                                             │                  │
                                             └── the VM's rain directory (read-only) ──┘
                                                 (`DEPLOY_RAIN_DIR` in `deploy/.env`)
```

- `server/`: Python 3.12, FastAPI, rasterio, numpy, Pillow. One container, no state, no database.
  It reads the rain directory read-only (mounted as `/data/rain`).
- nginx: `location ^~ <base>api/` proxies to the container (replacing today's proxy to Cloud Run).
  `location ~ ^<base>tiles/(week|season|year)/(\d+)/(\d+)/(\d+)\.png$` proxies to TiTiler
  `/cog/tiles/WebMercatorQuad/$z/$x/$y.png?url=/data/rain/rain_$layer.tif&<query>`; only these three
  files can be requested. An optional `limit_req` directive from `.env` (`DEPLOY_TILES_LIMIT_REQ`).
- Deploy: `deploy/deploy.sh` also builds the server image and (re)starts it with
  `deploy/docker-compose.yml`. New `.env` keys: `DEPLOY_RAIN_DIR`, `DEPLOY_API_PORT`,
  `DEPLOY_TITILER_URL`; `DEPLOY_API_UPSTREAM` goes away. The nginx template gains the two routes.

## Data

Produced daily by `tools/rain/rain_daily.py` (prairie-layers) via `rain-daily.sh` on the VM:

| File | Content |
| --- | --- |
| `rain_daily_<cy>.tif` | crop year `cy` = Sep 1 (cy-1) .. Aug 31 cy; band i = day i, band description = date, nodata -9999 = day missing |
| `rain_week.tif`, `rain_season.tif`, `rain_year.tif` | sums for the three windows (tags: start, end, days_present) |
| `rain_stats.json` | `newest_day`, `crop_years`, per window `start`, `end`, `days_present`, percentiles p5 p50 p90 p95 p99, max |

Windows: week = newest day and the 6 before; season = Apr 1 .. newest, capped at Oct 31;
crop year = Sep 1 .. newest. History before 2026-10 (Thuan's Earth Engine export) has April to
November only.

## Endpoints

All responses `application/json`. POST bodies: `{"lat": <float>, "lon": <float>}`.

| Endpoint | Response | Source |
| --- | --- | --- |
| `POST /precipitation_values` | `{"weekly_precipitation": "Last 7 days: 8.5mm", "seasonal_precipitation": "Apr 01 - Oct 31: 408.7mm", "yearly_precipitation": "Sept 01 - today: 144.6mm"}` | one pixel of each window COG; dates from `rain_stats.json` ("today" while the window is still open, the end date once it is capped) |
| `POST /daily_precipitation` | `{"2026-11-25": {"precip": 0.03}, ... 7 days, newest first}` | the current crop-year stack, bands of the last 7 days |
| `POST /season_comparison` | `{"data": [{"year": 2020, "precip_sum": 271.6, "precip_sum_to_now": 271.6}, ...]}` | last 7 seasons incl. the current one; `precip_sum` = Apr 1 .. Oct 31 (to newest day for the current one), `precip_sum_to_now` = Apr 1 .. the newest day's calendar day, capped at Oct 31 |
| `POST /year_comparison` | same shape, `year` = crop-year label | last 7 crop years; **April to November only, every year alike** (no winter data before 2026-10); `_to_now` = up to the newest day's calendar position in the crop year |
| `GET /legend_info` | per layer `weeklyRain` / `seasonRain` / `yearRain`: `title`, `uri`, `min`, `max`, `mode: "continuous"`, `breaks`, `palette` (the original 16-colour palette); added: `tiles` (URL template `<base>tiles/<layer>/{z}/{x}/{y}.png?<colormap query>`), `as_of` (newest day) | `rain_stats.json` |
| `GET /legend/<layer>.png` | the legend gradient image that `uri` points to | palette |
| `GET /version` | `{"web": {"minimumRequiredVersion": "1.1.0"}, "ios": {...}, "android": {...}}` | constant |
| `GET /health` | `{"ok": true, "newest_day": ...}` | `rain_stats.json` |

Values in mm, one decimal (daily: two). A missing day contributes nothing to a sum; 404 when no
window has data at the point; a single empty window shows 0.0mm.

`uri` and `tiles` are site-relative paths; a client on another host must prefix them with the
server's origin.

Breaks (as the current API): weekly 0 .. p90, season and year p5 .. p95; the range is widened to a
"nice" step (1, 2, 5, 10, 20, 25, 50, 100 ...) so there are at most 8 classes. `min`/`max` strings:
`"0mm"`, `"≤250mm"`, `"≥550mm"`.

## Tiles

The colormap, stretch and resampling rules of the `tiles` template in `legend_info` are in
docs/specs/2026-11-27-prairie-layers-look-design.md. Rain tiles exist to zoom 10; Leaflet scales
them.

## Frontend

- `HomePage` fetches `legend_info` once and passes it to `MapView` (tile templates) and `Legend`.
- `MapView`: `LAYER_URLS` come from `legend_info`; the Google bucket URLs are removed.
- Logos: the five images move into `public/logos/`, referenced via `import.meta.env.BASE_URL`.
- Crop-year chart: subtitle "April to November only".
- `apiConfig.js` default stays the Cloud Run URL for the hosted build; the VM build sets
  `VITE_API_BASE_URL=<base>api` as now.

## Errors

| Case | Response |
| --- | --- |
| lat/lon missing or out of range | 422 (FastAPI validation) |
| point outside the raster or nodata in every day of the window | 404 `{"detail": "No data at this location"}` |
| a required raster or `rain_stats.json` missing or unreadable | 503 `{"detail": "Rain data unavailable"}` |

The frontend shows `detail` from error responses (see item 5).

## Performance

A point read is one pixel per band; a crop-year stack has 365 bands in 64 px blocks, a few tens of
ms per stack. The comparison endpoints read 7 stacks. `rain_stats.json` is cached per process and re-read when its
mtime changes; rasters are opened per request (about 1 ms), so a rewritten file is picked up
immediately. Target: under 1 s per request on
the VM.

## Testing

- `server/tests/`: pytest with a synthetic rain directory (small stacks with known values, built by
  a fixture) covering each endpoint's shape and arithmetic, the window rules, the April-November
  rule, nodata handling and the breaks function.
- `server/tools/compare_api.py`: the same points against the old API and the new one, printing
  the differences; run once before switching the frontend. Differences in history are expected
  (different sources), the weekly totals should match to 0.1 mm as the pipeline check did.
- Manual: the app in a browser on the VM address, all three layers, tap, three charts, legend.

## Rollback

Revert the range of commits that introduced `server/`, the tiles route and the frontend changes on
`main`, restore the previous `.env` keys on the server before the cron deploy picks it up (or run
`deploy.sh --force`), and remove the API container with
`docker compose -f deploy/docker-compose.yml down`. The original Google resources are untouched by
this work.

## Result (2026-11-26)

`server/tools/compare_api.py` against the original Cloud Run API, 8 points: weekly totals agree to
0.0 mm (identical at all 8 points); seasonal totals for 2026 differ by up to 9.1 mm (Calgary, 350.8
against 359.9; the other 7 points within 3.1 mm); crop-year history differs as expected (April to
November only; different sources before 2026-08): 30 to 126 mm less per past crop year, the current
crop year within 5 mm. The app now uses only the VM.
