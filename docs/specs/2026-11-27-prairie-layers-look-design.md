# Rain overlays and legend in the Prairie Layers style

Date: 2026-11-27. Status: approved (Fang).

## Goal

The three rain overlays, the legend and the layer picker of the web app look like the rain maps
of the Prairie Layers site, which is served from the same rasters: the YlGnBu ramp with the dry
end fading to the basemap, bilinear resampling, a compact dark-green glass legend with a gradient
bar, and a gradient swatch beside each layer name.

## Overlays (API `legend_info` and the tiles route)

- Ramp, low to high: `#ffffd9 #c7e9b4 #41b6c4 #225ea8 #0c2c84` (five stops, as `layers.json` of
  Prairie Layers).
- Stretch: `rescale=0,<hi>` where `<hi>` is the top of `nice_breaks(0, p95)` of the window's
  region-wide percentiles in `rain_stats.json`; it changes daily and per layer. (Prairie Layers
  stretches to the pixels on screen; that needs a statistics endpoint and is left for later.)
- Colormap: 64 equal intervals over 0..255 (TiTiler applies it after `rescale`), colours
  interpolated between the stops; the lowest 12 % of the range fades in from transparent (alpha
  `min(255, round(255 * (i + 1) / (64 * 0.12)))`), so dry ground shows the basemap.
- `resampling=bilinear` so the 2.5 km pixels blend instead of showing as blocks.
- The tiles template in `legend_info` carries `resampling`, `rescale` and `colormap`; nginx
  forwards exactly those three query parameters to TiTiler (`$arg_resampling`, `$arg_rescale`,
  `$arg_colormap`) and nothing else.
- `legend_info` per layer keeps `title`, `uri`, `min`, `max`, `mode`, `breaks`, `palette`,
  `tiles`, `as_of` (the palette is now the five stops, `breaks` is `nice_breaks(0, p95)`,
  `min` is `0mm`, `max` is `≥<hi>mm`) and adds `label` (`Last 7 days`, `Growing season`,
  `Crop year`), `units` (`mm`) and `range` (`[0, hi]`). The legend PNG draws the interpolated
  ramp (opaque).

## Legend (frontend)

Same place as today (top centre of the map), styled as the Prairie Layers legend box:

- Box: `rgba(29, 92, 58, 0.92)` with `backdrop-filter: blur(10px)`, radius 8 px, shadow
  `0 8px 26px rgba(0, 0, 0, 0.28)`, text `#f5f2e8`, width 220 px, padding 8 px 10 px.
- Title line: the layer `label` in 600 12 px with `letter-spacing 0.02em`, then the units in a
  dimmer span (`#d3dfd6`, weight 400; lighter than Prairie Layers' `#b9cbbd` so it keeps 4.5:1 contrast
  over a light basemap).
- Bar: 12 px high, radius 4 px, `linear-gradient(90deg, <palette>)` drawn in CSS from the
  palette (the PNG is no longer used by the web app).
- Ends: `0` left, `≥ <hi>` right, 11 px, `#d3dfd6`, tabular numerals. The Retry button uses
  `#ffd98a` for the same reason.
- Loading and error states keep their behaviour with colours that read on the dark box.

## Layer picker

Each option in "Select Layer" gets a 34 px square swatch on the left, radius 6 px, 1 px light
ring, `linear-gradient(135deg, <palette>)`, built from `legend_info` (no second copy of the ramp
in the frontend).

## Auto-stretch and cropland outline (added the same day)

The shared map kit (`site/kit/` of the prairie-layers repo, copied into `src/kit/` at the tag in
`kit.version`) provides the pieces both apps use: ramp and colormap, TiTiler query, the on-screen
range controller (`createDra`) and the outline overlay. The app runs auto-stretch by default: after
each pan or zoom the 2nd..98th percentile of the pixels on screen comes from `<base>stats/<layer>`
(nginx proxies a POST with the screen polygon to TiTiler statistics for that one COG), the tile
URL's `rescale` is rewritten to `0,<p98>` (fade-low keeps the low end at 0) and the legend ends
follow. Auto-stretch is always on in the app (no toggle; the kit's controller is created enabled).
The cropland outline (`<base>vector/cropland_outline.geojson`) is drawn on top in
Prairie Layers' gold with its weight-by-zoom steps.

## Out of scope

The mobile app; the Prairie Layers rain card.

## Charts from the Prairie Layers rain card (added 2026-11-27, later)

- The legend's Auto-stretch toggle is removed from the app; auto-stretch stays on.
- The three charts behind the point values (daily bars, growing-season comparison, crop-year
  comparison) are the Prairie Layers rain card charts: 30 days of daily bars with the last 7 days
  marked, and the cumulative season / crop year against up to six earlier years (gold line = this
  year, dashed = the earlier years' average, one colour per year, tap a year label to bring it to
  the front, slide across to read a date). Inline SVG from the kit (`rainseries.js` for the data,
  `raincharts.js` for the drawing, `rain-charts.css` for the look); Prairie Layers' own rain card
  uses the same modules.
- Data: the app reads the daily series at the tapped point straight from TiTiler through
  `<base>point/<crop year>/<lon>,<lat>` (one request per crop-year stack, as Prairie Layers does)
  and the window definitions from `<base>api/rain_stats`. The three totals still come from
  `precipitation_values`.
- Look: the charts take their colours from CSS variables set by the host. In the app they sit in
  the white modal sheet (dark ink, muted grey, amber accent that reads on white); nothing turns
  green except the map legend. The recharts dependency goes.
