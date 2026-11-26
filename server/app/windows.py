"""Date windows of the Virtual Rain Gauge and sums over daily series.

Season = Apr 1 .. Oct 31. Crop year cy = Sep 1 (cy-1) .. Aug 31 cy, labelled by the year it ends in.
History before 2026-10 has April to November only, so crop-year comparisons use APRIL_TO_NOVEMBER.
"""
from collections.abc import Callable
from datetime import date

APRIL_TO_NOVEMBER: frozenset[int] = frozenset(range(4, 12))


def season_window(year: int) -> tuple[date, date]:
    """The growing season of `year`: Apr 1 .. Oct 31."""
    return date(year, 4, 1), date(year, 10, 31)


def crop_year_window(cy: int) -> tuple[date, date]:
    """Crop year `cy`: Sep 1 of the previous year .. Aug 31 of `cy`."""
    return date(cy - 1, 9, 1), date(cy, 8, 31)


def same_position(newest: date, start: date, end: date) -> date:
    """The day of [start, end] with newest's month and day, capped at end (before the window -> start).

    Feb 29 becomes Feb 28 in a year without one.
    """
    for year in (start.year, end.year):
        try:
            candidate = date(year, newest.month, newest.day)
        except ValueError:  # Feb 29 in a year without one
            candidate = date(year, 2, 28)
        if start <= candidate <= end:
            return candidate
    return end if newest > end else start


def sum_days(
    series: dict[date, float],
    start: date,
    end: date,
    months: frozenset[int] | None = None,
) -> float:
    """Sum of the days in [start, end], both inclusive, optionally only those whose calendar month is in `months`."""
    return float(
        sum(v for d, v in series.items()
            if start <= d <= end and (months is None or d.month in months))
    )


def comparison_rows(
    series: dict[date, float],
    years: list[int],
    window: Callable[[int], tuple[date, date]],
    newest: date,
    months: frozenset[int] | None,
) -> list[dict[str, int | float]]:
    """One row {"year", "precip_sum", "precip_sum_to_now"} per entry of `years`, sums rounded to 1 decimal.

    `window` is called for each year to get its (start, end); "to now" runs up to the same position as `newest`.
    """
    rows = []
    for y in years:
        start, end = window(y)
        to_now = same_position(newest, start, end)
        rows.append(
            {
                "year": y,
                "precip_sum": round(sum_days(series, start, end, months), 1),
                "precip_sum_to_now": round(sum_days(series, start, to_now, months), 1),
            }
        )
    return rows
