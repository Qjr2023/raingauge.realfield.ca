import io
import json
from urllib.parse import unquote

import pytest
from PIL import Image

from app.legend import PALETTE, colormap_query, legend_info, legend_png, nice_breaks

STATS = {
    "newest_day": "2026-11-25",
    "crop_years": [2025, 2026, 2027],
    "layers": {
        "week": {"start": "2026-11-19", "end": "2026-11-25", "p5": 0.0, "p90": 15.2, "p95": 20.2},
        "season": {"start": "2026-04-01", "end": "2026-10-31", "p5": 295.1, "p90": 485.6, "p95": 509.2},
        "year": {"start": "2026-09-01", "end": "2026-11-25", "p5": 53.7, "p90": 153.5, "p95": 164.0},
    },
}


def test_palette_has_16_colours():
    assert len(PALETTE) == 16 and PALETTE[0] == "#e0d8d3" and PALETTE[-1] == "#221b38"


def test_nice_breaks_match_the_current_api():
    assert nice_breaks(0.0, 15.2) == [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0]
    assert nice_breaks(295.1, 509.2) == [250.0, 300.0, 350.0, 400.0, 450.0, 500.0, 550.0]
    assert nice_breaks(0.0, 15.2, max_classes=4) == [0.0, 5.0, 10.0, 15.0, 20.0]
    assert nice_breaks(53.7, 164.0) == [40.0, 60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0]


def test_nice_breaks_degenerate_range():
    assert nice_breaks(0.0, 0.0) == [0.0, 1.0]
    assert nice_breaks(0.0, 123456.0) == [0.0, 123456.0]


def test_colormap_query_is_16_intervals_with_open_ends():
    q = colormap_query([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0])
    assert q.startswith("colormap=")
    intervals = json.loads(unquote(q[len("colormap="):]))
    assert len(intervals) == 16
    assert intervals[0][0][0] < -1e5 and intervals[-1][0][1] > 1e5
    assert intervals[0][1] == [224, 216, 211, 255]
    assert intervals[1][0] == [1.0, 2.0]


def test_legend_info_shape():
    info = legend_info(STATS, "/raingauge/")
    assert set(info) == {"weeklyRain", "seasonRain", "yearRain"}
    w = info["weeklyRain"]
    assert w["title"] == "Last weeks precipitation"
    assert w["min"] == "0mm" and w["max"] == "≥16mm" and w["mode"] == "continuous"
    assert w["breaks"] == [0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0, 14.0, 16.0]
    assert w["palette"] == PALETTE
    assert w["uri"] == "/raingauge/api/legend/weeklyRain.png"
    assert w["tiles"].startswith("/raingauge/tiles/week/{z}/{x}/{y}.png?colormap=")
    assert w["tiles"].endswith(colormap_query(w["breaks"]))
    assert w["as_of"] == "2026-11-25"
    s = info["seasonRain"]
    assert s["min"] == "≤250mm" and s["max"] == "≥550mm"
    assert s["title"] == "Growing Season Precipitation (April 1 to now)."
    y = info["yearRain"]
    assert y["title"] == "Crop Year Precipitation (Sept 2026 to now)."
    assert y["tiles"].startswith("/raingauge/tiles/year/")


def test_legend_png_is_a_png():
    png = legend_png("weeklyRain")
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    img = Image.open(io.BytesIO(png))
    assert img.size == (256, 16)
    assert img.getpixel((0, 0)) == (224, 216, 211, 255)
    assert img.getpixel((255, 0)) == (34, 27, 56, 255)
    with pytest.raises(KeyError):
        legend_png("nope")
