from datetime import date, timedelta

from app.windows import (
    APRIL_TO_NOVEMBER,
    comparison_rows,
    crop_year_window,
    same_position,
    season_window,
    sum_days,
)


def test_season_window():
    assert season_window(2026) == (date(2026, 4, 1), date(2026, 10, 31))


def test_crop_year_window():
    assert crop_year_window(2027) == (date(2026, 9, 1), date(2027, 8, 31))


def test_same_position_in_season_is_capped_at_end():
    start, end = season_window(2025)
    assert same_position(date(2026, 11, 25), start, end) == date(2025, 10, 31)
    assert same_position(date(2026, 6, 3), start, end) == date(2025, 6, 3)


def test_same_position_in_crop_year_picks_the_right_calendar_year():
    start, end = crop_year_window(2026)  # Sep 2025 .. Aug 2026
    assert same_position(date(2026, 11, 25), start, end) == date(2025, 11, 25)
    assert same_position(date(2027, 3, 2), start, end) == date(2026, 3, 2)


def test_same_position_feb_29():
    start, end = crop_year_window(2027)  # Sep 2026 .. Aug 2027, 2027 is not a leap year
    assert same_position(date(2028, 2, 29), start, end) == date(2027, 2, 28)
    assert same_position(date(2028, 2, 29), *crop_year_window(2028)) == date(2028, 2, 29)


def test_sum_days_counts_only_days_in_window_and_months():
    series = {
        date(2026, 3, 31): 10.0,
        date(2026, 4, 1): 1.0,
        date(2026, 7, 15): 2.5,
        date(2026, 12, 1): 100.0,
    }
    assert sum_days(series, date(2026, 4, 1), date(2026, 12, 31)) == 103.5
    assert sum_days(series, date(2026, 4, 1), date(2026, 12, 31), APRIL_TO_NOVEMBER) == 3.5
    assert sum_days({}, date(2026, 4, 1), date(2026, 12, 31)) == 0.0


def test_comparison_rows_full_and_to_now():
    # 0.07 mm every day in season 2025, 2 mm in season 2026 up to Jun 30 (newest day)
    series = {}
    for y, v, last in ((2025, 0.07, date(2025, 10, 31)), (2026, 2.0, date(2026, 6, 30))):
        d = date(y, 4, 1)
        while d <= last:
            series[d] = v
            d += timedelta(days=1)
    rows = comparison_rows(series, [2025, 2026], season_window, date(2026, 6, 30), None)
    assert rows == [
        {"year": 2025, "precip_sum": 15.0, "precip_sum_to_now": 6.4},
        {"year": 2026, "precip_sum": 182.0, "precip_sum_to_now": 182.0},
    ]


def test_comparison_rows_crop_year_april_to_november():
    series = {}
    d = date(2025, 9, 1)
    while d <= date(2026, 8, 31):
        series[d] = 1.0
        d += timedelta(days=1)
    rows = comparison_rows(series, [2026], crop_year_window, date(2026, 8, 31), APRIL_TO_NOVEMBER)
    # Sep..Nov 91 days + Apr..Aug 153 days
    assert rows == [{"year": 2026, "precip_sum": 244.0, "precip_sum_to_now": 244.0}]
