"""Point reads of the rain rasters the pipeline writes (docs/specs/2026-11-26-vm-api-design.md).

rain_week/season/year.tif: one band, the window sum. rain_stats.json: newest day, crop years,
window dates and percentiles. (The daily stacks rain_daily_<cy>.tif are read by TiTiler through the
point route, not here.)
"""
import json
import math
from datetime import date
from pathlib import Path

import rasterio
from rasterio.errors import RasterioIOError
from rasterio.windows import Window


class DataUnavailable(Exception):
    """A required file is missing or unreadable."""


class RainData:
    """Reads one pixel column of the rain rasters in `rain_dir`; caches rain_stats.json by mtime."""

    def __init__(self, rain_dir: Path) -> None:
        self.rain_dir = Path(rain_dir)
        self._stats: dict | None = None
        self._stats_mtime: float | None = None

    def stats(self) -> dict:
        """rain_stats.json as a dict, re-read when the file's mtime changes."""
        p = self.rain_dir / "rain_stats.json"
        try:
            mtime = p.stat().st_mtime
            if self._stats is None or mtime != self._stats_mtime:
                stats = json.loads(p.read_text())
                if (not {"newest_day", "crop_years", "layers"} <= stats.keys()
                        or not stats["crop_years"]):
                    raise DataUnavailable("rain_stats.json: incomplete")
                self._stats, self._stats_mtime = stats, mtime
        except (OSError, ValueError) as e:
            raise DataUnavailable(f"rain_stats.json: {e}") from e
        return self._stats

    def newest_day(self) -> date:
        """The newest day in the data, from rain_stats.json."""
        return date.fromisoformat(self.stats()["newest_day"])

    def _column(
        self, path: Path, lon: float, lat: float
    ) -> tuple[list[float], list[str | None], float | None] | None:
        """Band values, band descriptions and nodata at (lon, lat); None if outside the grid."""
        try:
            with rasterio.open(path) as ds:
                row, col = ds.index(lon, lat)
                if not (0 <= row < ds.height and 0 <= col < ds.width):
                    return None
                values = ds.read(window=Window(col, row, 1, 1))[:, 0, 0]
                return [float(v) for v in values], list(ds.descriptions), ds.nodata
        except RasterioIOError as e:
            raise DataUnavailable(f"{path.name}: {e}") from e

    @staticmethod
    def _present(v: float, nodata: float | None) -> bool:
        return not math.isnan(v) and (nodata is None or v != nodata)

    def window_value(self, short: str, lon: float, lat: float) -> float | None:
        """The week/season/year sum at a point; None outside the grid or where there is no data."""
        col = self._column(self.rain_dir / f"rain_{short}.tif", lon, lat)
        if col is None:
            return None
        values, _, nodata = col
        return values[0] if self._present(values[0], nodata) else None
