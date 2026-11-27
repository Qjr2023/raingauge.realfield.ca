"""Legend entries, class breaks and the TiTiler colormap for the three rain overlays.

Breaks: 0 .. p95 of the window, widened to a nice step so there are at most 8 classes. Colours:
the five YlGnBu stops of Prairie Layers' layers.json, interpolated linearly; the lowest 12 % of
the stretch fades in from transparent so dry ground shows the basemap.
"""
import io
import json
import math
from urllib.parse import quote

from PIL import Image

PALETTE: list[str] = ["#ffffd9", "#c7e9b4", "#41b6c4", "#225ea8", "#0c2c84"]
LAYERS: dict[str, str] = {"weeklyRain": "week", "seasonRain": "season", "yearRain": "year"}
LABELS: dict[str, str] = {
    "weeklyRain": "Last 7 days", "seasonRain": "Growing season", "yearRain": "Crop year",
}
_STEPS = (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000)
_RAMP_INTERVALS = 64
_FADE_FRACTION = 0.12


def nice_breaks(lo: float, hi: float, max_classes: int = 8) -> list[float]:
    """Class edges from lo to hi, widened outward to the smallest nice step giving <= max_classes."""
    for step in _STEPS:
        lo_r = math.floor(lo / step) * step
        hi_r = math.ceil(hi / step) * step
        if hi_r <= lo_r:
            hi_r = lo_r + step
        n = (hi_r - lo_r) // step
        if n <= max_classes:
            return [float(lo_r + i * step) for i in range(n + 1)]
    # only if the range exceeds 8 x 1000 mm: keep the raw edges
    return [float(lo), float(hi)]


def _rgb(hex_colour: str) -> list[int]:
    h = hex_colour.lstrip("#")
    return [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)]


def _ramp_rgb(i: int, n: int = _RAMP_INTERVALS) -> list[int]:
    """Colour of interval i of n, interpolated linearly between the palette stops."""
    stops = [_rgb(c) for c in PALETTE]
    x = ((i + 0.5) / n) * (len(stops) - 1)
    k = min(math.floor(x), len(stops) - 2)
    t = x - k
    return [round(stops[k][j] + (stops[k + 1][j] - stops[k][j]) * t) for j in range(3)]


def ramp_colormap(fade_low: bool = True) -> list:
    """TiTiler interval colormap over 0..255: 64 intervals of the ramp, the low end fading in."""
    n = _RAMP_INTERVALS
    out = []
    for i in range(n):
        alpha = min(255, round(255 * (i + 1) / (n * _FADE_FRACTION))) if fade_low else 255
        out.append([[i * 256 / n, (i + 1) * 256 / n], _ramp_rgb(i, n) + [alpha]])
    return out


def tile_query(breaks: list[float]) -> str:
    """The tiles query string: bilinear resampling, stretch 0..hi and the ramp colormap."""
    colormap = quote(json.dumps(ramp_colormap(), separators=(",", ":")))
    return f"resampling=bilinear&rescale=0,{breaks[-1]:g}&colormap={colormap}"


# Titles verbatim from the original API (including "Last weeks" without apostrophe),
# for compatibility.
def _title(layer: str, stats: dict) -> str:
    if layer == "weeklyRain":
        return "Last weeks precipitation"
    if layer == "seasonRain":
        return "Growing Season Precipitation (April 1 to now)."
    start_year = stats["layers"]["year"]["start"][:4]
    return f"Crop Year Precipitation (Sept {start_year} to now)."


def _breaks_for(layer: str, stats: dict) -> list[float]:
    return nice_breaks(0.0, float(stats["layers"][LAYERS[layer]]["p95"]))


def _mm(v: float) -> str:
    return f"{int(v)}mm" if float(v).is_integer() else f"{v:g}mm"


def legend_info(stats: dict, public_base: str) -> dict:
    """The /legend_info body: per layer, title, label, legend image, range, palette, tiles,
    the statistics route for auto-stretch, the rain_stats and point routes for the charts, the
    fade-low flag and the cropland outline."""
    base = public_base if public_base.endswith("/") else public_base + "/"
    out = {}
    for layer, short in LAYERS.items():
        breaks = _breaks_for(layer, stats)
        hi = breaks[-1]
        out[layer] = {
            "title": _title(layer, stats),
            "label": LABELS[layer],
            "uri": f"{base}api/legend/{layer}.png",
            "min": _mm(breaks[0]),
            "max": "≥" + _mm(hi),
            "units": "mm",
            "range": [0.0, hi],
            "mode": "continuous",
            "breaks": breaks,
            "palette": PALETTE,
            "tiles": f"{base}tiles/{short}/{{z}}/{{x}}/{{y}}.png?{tile_query(breaks)}",
            "stats": f"{base}stats/{short}",
            "rain_stats": f"{base}api/rain_stats",
            "point": f"{base}point/{{cy}}/{{lon}},{{lat}}",
            "fade_low": True,
            "outline": f"{base}vector/cropland_outline.geojson",
            "as_of": stats["newest_day"],
        }
    return out


def legend_png(layer: str) -> bytes:
    """The same 256 x 16 bar of the interpolated ramp for every layer (left = low, opaque).

    `layer` is checked so the route can answer 404.
    """
    if layer not in LAYERS:
        raise KeyError(layer)
    width, height = 256, 16
    row = [tuple(_ramp_rgb(i, width)) + (255,) for i in range(width)]
    img = Image.new("RGBA", (width, height))
    img.putdata(row * height)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
