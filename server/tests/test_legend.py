import io
import json
from urllib.parse import unquote

import pytest
from PIL import Image

from app.legend import PALETTE, legend_info, legend_png, nice_breaks, ramp_colormap, tile_query

STATS = {
    "newest_day": "2026-11-25",
    "crop_years": [2025, 2026, 2027],
    "layers": {
        "week": {"start": "2026-11-19", "end": "2026-11-25", "p5": 0.0, "p90": 15.2, "p95": 20.2},
        "season": {"start": "2026-04-01", "end": "2026-10-31", "p5": 295.1, "p90": 485.6, "p95": 509.2},
        "year": {"start": "2026-09-01", "end": "2026-11-25", "p5": 53.7, "p90": 153.5, "p95": 164.0},
    },
}


def test_palette_is_the_five_ylgnbu_stops():
    assert PALETTE == ["#ffffd9", "#c7e9b4", "#41b6c4", "#225ea8", "#0c2c84"]


def test_nice_breaks():
    assert nice_breaks(0.0, 15.2) == [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0]
    assert nice_breaks(295.1, 509.2) == [250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0]
    assert nice_breaks(0.0, 15.2, max_classes=4) == [0.0, 5.0, 10.0, 15.0, 20.0]
    assert nice_breaks(53.7, 164.0) == [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0]


def test_nice_breaks_degenerate_range():
    assert nice_breaks(0.0, 0.0) == [0.0, 1.0]
    assert nice_breaks(0.0, 123456.0) == [0.0, 123456.0]


def test_ramp_colormap_fades_in_over_the_low_end():
    cm = ramp_colormap()
    assert len(cm) == 64
    assert cm[0][0] == [0.0, 4.0]
    assert cm[-1][0][1] == 256
    assert cm[0][1] == [253, 254, 216, 33]  # alpha min(255, round(255 / 7.68))
    assert all(entry[1][3] == 255 for entry in cm[8:])
    # the last interval is sampled at its midpoint (x = 3.96875 of 4), just short of the last stop
    assert cm[-1][1] == [13, 46, 133, 255]
    assert all(entry[1][3] == 255 for entry in ramp_colormap(fade_low=False))


def test_tile_query_carries_resampling_rescale_and_colormap():
    q = tile_query([0.0, 25.0])
    assert q.startswith("resampling=bilinear&rescale=0,25&colormap=")
    intervals = json.loads(unquote(q.split("colormap=", 1)[1]))
    assert len(intervals) == 64
    assert intervals == ramp_colormap()


def test_legend_info_shape():
    info = legend_info(STATS, "/raingauge/")
    assert set(info) == {"weeklyRain", "seasonRain", "yearRain"}
    w = info["weeklyRain"]
    assert w["title"] == "Last weeks precipitation"
    assert w["label"] == "Last 7 days" and w["units"] == "mm"
    assert w["min"] == "0mm" and w["max"] == "≥25mm" and w["mode"] == "continuous"
    # weekly uses p95 like the other layers (20.2 -> step 5)
    assert w["breaks"] == [0.0, 5.0, 10.0, 15.0, 20.0, 25.0]
    assert w["range"] == [0.0, 25.0]
    assert w["palette"] == PALETTE
    assert w["uri"] == "/raingauge/api/legend/weeklyRain.png"
    assert w["tiles"].startswith("/raingauge/tiles/week/{z}/{x}/{y}.png?resampling=bilinear&")
    assert w["tiles"].endswith(tile_query(w["breaks"]))
    assert w["as_of"] == "2026-11-25"
    s = info["seasonRain"]
    assert s["label"] == "Growing season"
    assert s["min"] == "0mm" and s["max"] == "≥600mm" and s["range"] == [0.0, 600.0]
    assert s["title"] == "Growing Season Precipitation (April 1 to now)."
    y = info["yearRain"]
    assert y["label"] == "Crop year"
    assert y["range"] == [0.0, 175.0]
    assert y["title"] == "Crop Year Precipitation (Sept 2026 to now)."
    assert y["tiles"].startswith("/raingauge/tiles/year/")


def test_legend_png_is_the_opaque_ramp():
    png = legend_png("weeklyRain")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    img = Image.open(io.BytesIO(png))
    assert img.size == (256, 16)
    assert img.getpixel((0, 0)) == (255, 255, 217, 255)
    assert img.getpixel((255, 0)) == (12, 44, 132, 255)
    assert img.getpixel((255, 15)) == (12, 44, 132, 255)
    with pytest.raises(KeyError):
        legend_png("nope")
