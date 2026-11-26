import json
import os
import time
from datetime import date

import pytest

from app.rain_data import DataUnavailable, RainData
from tests.conftest import NODATA_PIXEL, OUTSIDE, TARGET, _write


def test_stats_and_newest_day(rain_dir):
    rd = RainData(rain_dir)
    assert rd.stats()["crop_years"] == [2025, 2026, 2027]
    assert rd.newest_day() == date(2026, 11, 25)


def test_stats_missing_raises(tmp_path):
    with pytest.raises(DataUnavailable):
        RainData(tmp_path).stats()


def test_stats_incomplete_raises(tmp_path):
    (tmp_path / "rain_stats.json").write_text(json.dumps({"newest_day": "2026-11-25"}))
    with pytest.raises(DataUnavailable):
        RainData(tmp_path).stats()


def test_stats_cache_refreshes_when_file_changes(rain_dir, tmp_path):
    p = tmp_path / "rain_stats.json"
    p.write_text((rain_dir / "rain_stats.json").read_text())
    rd = RainData(tmp_path)
    assert rd.newest_day() == date(2026, 11, 25)
    p.write_text(json.dumps({**json.loads(p.read_text()), "newest_day": "2026-11-26"}))
    later = time.time() + 5
    os.utime(p, (later, later))
    assert rd.newest_day() == date(2026, 11, 26)


def test_stack_with_bad_band_description_raises(tmp_path):
    _write(tmp_path / "rain_daily_2030.tif", [("not a date", 1.0)], {})
    with pytest.raises(DataUnavailable):
        RainData(tmp_path).stack_series(2030, *TARGET)


def test_window_value(rain_dir):
    rd = RainData(rain_dir)
    assert rd.window_value("week", *TARGET) == 7.0
    assert rd.window_value("season", *TARGET) == 214.0
    assert rd.window_value("year", *TARGET) == 86.0
    assert rd.window_value("week", *OUTSIDE) is None
    assert rd.window_value("week", *NODATA_PIXEL) is None


def test_window_value_missing_file(tmp_path):
    with pytest.raises(DataUnavailable):
        RainData(tmp_path).window_value("week", *TARGET)


def test_stack_series_present_days_only(rain_dir):
    rd = RainData(rain_dir)
    s = rd.stack_series(2027, *TARGET)
    assert len(s) == 86
    assert s[date(2026, 9, 1)] == 1.0 and s[date(2026, 11, 25)] == 1.0
    assert date(2026, 11, 26) not in s
    assert rd.stack_series(2027, *OUTSIDE) == {}
    assert rd.stack_series(2027, *NODATA_PIXEL) == {}
    assert rd.stack_series(1999, *TARGET) == {}


def test_series_for_years_merges(rain_dir):
    rd = RainData(rain_dir)
    s = rd.series_for_years([2026, 2027], *TARGET)
    assert s[date(2026, 4, 1)] == 2.0 and s[date(2026, 9, 1)] == 1.0
    assert date(2026, 1, 15) not in s  # winter day absent in the history stack
