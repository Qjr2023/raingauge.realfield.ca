"""Legend entries, class breaks and the TiTiler colormap for the three rain overlays.

Rules as in the original API: weekly 0 .. p90, season and crop year p5 .. p95, widened to a nice
step so there are at most 8 classes. Colours: the original 16-stop ramp (cmocean "rain").
"""
import io
import json
import math
from urllib.parse import quote

from PIL import Image

PALETTE: list[str] = [
    "#e0d8d3", "#d8c7b4", "#c9ba96", "#b0b188", "#95a87e", "#799f76", "#5b9770", "#388d6d",
    "#17816e", "#05746e", "#07656b", "#155766", "#20485d", "#253850", "#252a44", "#221b38",
]
LAYERS: dict[str, str] = {"weeklyRain": "week", "seasonRain": "season", "yearRain": "year"}
_STEPS = (1, 2, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000)
_FAR = 1e9


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


def _rgba(hex_colour: str) -> list[int]:
    h = hex_colour.lstrip("#")
    return [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255]


def colormap_query(breaks: list[float]) -> str:
    """TiTiler interval colormap: 16 equal intervals from min to max, open at both ends."""
    lo, hi = breaks[0], breaks[-1]
    n = len(PALETTE)
    edges = [lo + (hi - lo) * i / n for i in range(n + 1)]
    edges[0], edges[-1] = -_FAR, _FAR
    intervals = [[[edges[i], edges[i + 1]], _rgba(PALETTE[i])] for i in range(n)]
    return "colormap=" + quote(json.dumps(intervals, separators=(",", ":")))


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
    w = stats["layers"][LAYERS[layer]]
    if layer == "weeklyRain":
        return nice_breaks(0.0, float(w["p90"]))
    return nice_breaks(float(w["p5"]), float(w["p95"]))


def _mm(v: float) -> str:
    return f"{int(v)}mm" if float(v).is_integer() else f"{v:g}mm"


def legend_info(stats: dict, public_base: str) -> dict:
    """The /legend_info body: per layer, title, legend image, range, breaks, palette and tiles."""
    base = public_base if public_base.endswith("/") else public_base + "/"
    out = {}
    for layer, short in LAYERS.items():
        breaks = _breaks_for(layer, stats)
        out[layer] = {
            "title": _title(layer, stats),
            "uri": f"{base}api/legend/{layer}.png",
            "min": _mm(breaks[0]) if breaks[0] == 0 else "≤" + _mm(breaks[0]),
            "max": "≥" + _mm(breaks[-1]),
            "mode": "continuous",
            "breaks": breaks,
            "palette": PALETTE,
            "tiles": f"{base}tiles/{short}/{{z}}/{{x}}/{{y}}.png?{colormap_query(breaks)}",
            "as_of": stats["newest_day"],
        }
    return out


def legend_png(layer: str) -> bytes:
    """The same 256 x 16 bar of the 16 palette colours for every layer (left = low).

    `layer` is checked so the route can answer 404.
    """
    if layer not in LAYERS:
        raise KeyError(layer)
    bar = Image.new("RGBA", (16, 1))
    bar.putdata([tuple(_rgba(c)) for c in PALETTE])
    img = bar.resize((256, 16), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
