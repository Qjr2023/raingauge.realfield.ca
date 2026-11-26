"""A tiny synthetic rain directory with known values.

Grid: 10 x 10 pixels of 0.5 degrees, lon -110 .. -105, lat 55 .. 50 (EPSG:4326).
TARGET pixel (row 2, col 3): every present day has the value of its crop-year stack
(2025 -> 3 mm, 2026 -> 2 mm, 2027 -> 1 mm). NODATA_PIXEL (row 0, col 0) is nodata in every band.
Stacks 2025 and 2026 have April..November days only (like the imported history); stack 2027 has
Sep 1 .. Nov 25 2026 (the newest day), the rest of its bands nodata.
Window COGs at TARGET: week 7, season 214, year 86.
"""
import json
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

TARGET = (-108.25, 53.75)
OUTSIDE = (-100.0, 53.75)
NODATA_PIXEL = (-109.75, 54.75)
NEWEST = date(2026, 11, 25)
NODATA = -9999.0
_PROFILE = dict(
    driver="GTiff", dtype="float32", width=10, height=10, crs="EPSG:4326",
    transform=from_origin(-110.0, 55.0, 0.5, 0.5), nodata=NODATA,
)


def _days(start: date, end: date):
    d = start
    while d <= end:
        yield d
        d += timedelta(days=1)


def _write(path: Path, bands: list[tuple[str, float | None]], tags: dict) -> None:
    """bands: (description, value at TARGET or None for a nodata band)."""
    with rasterio.open(path, "w", count=len(bands), **_PROFILE) as dst:
        for i, (desc, value) in enumerate(bands, start=1):
            arr = np.full((10, 10), NODATA if value is None else value, dtype="float32")
            arr[0, 0] = NODATA
            dst.write(arr, i)
            dst.set_band_description(i, desc)
        dst.update_tags(**tags)


def _stack(path: Path, cy: int, value: float, present) -> None:
    start, end = date(cy - 1, 9, 1), date(cy, 8, 31)
    bands = [(d.isoformat(), value if present(d) else None) for d in _days(start, end)]
    _write(path, bands, {"crop_year": str(cy), "first_day": start.isoformat(), "units": "mm"})


@pytest.fixture(scope="session")
def rain_dir(tmp_path_factory) -> Path:
    d = tmp_path_factory.mktemp("rain")
    _stack(d / "rain_daily_2025.tif", 2025, 3.0, lambda x: 4 <= x.month <= 11)
    _stack(d / "rain_daily_2026.tif", 2026, 2.0, lambda x: 4 <= x.month <= 11)
    _stack(d / "rain_daily_2027.tif", 2027, 1.0, lambda x: x <= NEWEST)
    _write(d / "rain_week.tif", [("2026-11-19 to 2026-11-25", 7.0)],
           {"start": "2026-11-19", "end": "2026-11-25"})
    _write(d / "rain_season.tif", [("2026-04-01 to 2026-10-31", 214.0)],
           {"start": "2026-04-01", "end": "2026-10-31"})
    _write(d / "rain_year.tif", [("2026-09-01 to 2026-11-25", 86.0)],
           {"start": "2026-09-01", "end": "2026-11-25"})
    stats = {
        "newest_day": NEWEST.isoformat(),
        "generated": "2026-11-25T22:10:00+00:00",
        "crop_years": [2025, 2026, 2027],
        "layers": {
            "week": {"start": "2026-11-19", "end": "2026-11-25", "days": 7, "days_present": 7,
                     "p5": 0.0, "p50": 6.4, "p90": 15.2, "p95": 20.2, "p99": 33.9, "max": 62.2},
            "season": {"start": "2026-04-01", "end": "2026-10-31", "days": 214,
                       "days_present": 214, "p5": 295.1, "p50": 394.7, "p90": 485.6,
                       "p95": 509.2, "p99": 548.7, "max": 634.4},
            "year": {"start": "2026-09-01", "end": "2026-11-25", "days": 86, "days_present": 86,
                     "p5": 53.7, "p50": 105.2, "p90": 153.5, "p95": 164.0, "p99": 190.7,
                     "max": 279.6},
        },
    }
    (d / "rain_stats.json").write_text(json.dumps(stats))
    return d
