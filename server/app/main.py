"""Virtual Rain Gauge API served from the VM's own rasters.

Same request and response formats as the original Cloud Run API (api.realfield.ca), so the web app
and later the mobile app can use either.
"""
import logging
from datetime import date, timedelta

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import Settings, settings_from_env
from .legend import LAYERS, legend_info, legend_png
from .rain_data import DataUnavailable, RainData
from .windows import APRIL_TO_NOVEMBER, comparison_rows, crop_year_window, season_window

log = logging.getLogger(__name__)

YEARS_SHOWN = 7

# Verbatim copy of the original API's /version output for the mobile apps.
MOBILE_VERSIONS: dict[str, dict] = {
    "ios": {
        "minimumRequiredVersion": "1.0.6",
        "minimumBuildNumber": "1",
        "storeUrl": "https://apps.apple.com/app/virtual-rain-gauge",
    },
    "android": {
        "minimumRequiredVersion": "1.0.6",
        "minimumVersionCode": 1,
        "storeUrl": "https://play.google.com/store/apps/details?id=com.namtranhoai.rain_gauge_app",
    },
}


class Point(BaseModel):
    """A map location; the body of every POST endpoint."""
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


def no_data() -> HTTPException:
    """A fresh instance per raise: a reused one keeps every raise's traceback alive."""
    return HTTPException(status_code=404, detail="No data at this location")


def _month(d: date) -> str:
    # The original API writes "Sept", not "Sep".
    return "Sept" if d.month == 9 else d.strftime("%b")


def _window_text(stats: dict, short: str, value: float) -> str:
    """'Apr 01 - today: 408.7mm' while the window is open, 'Apr 01 - Oct 31: ...' once capped."""
    w = stats["layers"][short]
    start = date.fromisoformat(w["start"])
    end = date.fromisoformat(w["end"])
    end_text = "today" if w["end"] == stats["newest_day"] else f"{_month(end)} {end.day:02d}"
    return f"{_month(start)} {start.day:02d} - {end_text}: {value:.1f}mm"


def create_app(settings: Settings) -> FastAPI:
    """Build the app for the given settings (tests pass their own)."""
    app = FastAPI(title="Virtual Rain Gauge API", docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"]
    )
    data = RainData(settings.rain_dir)

    @app.exception_handler(DataUnavailable)
    async def _unavailable(request: Request, exc: DataUnavailable) -> JSONResponse:
        log.warning("rain data unavailable: %s", exc)
        return JSONResponse(status_code=503, content={"detail": "Rain data unavailable"})

    @app.get("/health")
    def health() -> dict:
        return {"ok": True, "newest_day": data.stats()["newest_day"]}

    @app.get("/version")
    def version() -> dict:
        return {"web": {"minimumRequiredVersion": settings.app_version}, **MOBILE_VERSIONS}

    @app.get("/legend_info")
    def legend() -> dict:
        return legend_info(data.stats(), settings.public_base)

    @app.get("/legend/{layer}.png")
    def legend_image(layer: str) -> Response:
        if layer not in LAYERS:
            raise HTTPException(status_code=404, detail="Unknown layer")
        return Response(
            content=legend_png(layer),
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    @app.post("/precipitation_values")
    def precipitation_values(p: Point) -> dict:
        stats = data.stats()
        values = {
            short: data.window_value(short, p.lon, p.lat) for short in ("week", "season", "year")
        }
        if all(v is None for v in values.values()):
            raise no_data()
        week = values["week"] or 0.0
        return {
            "weekly_precipitation": f"Last 7 days: {week:.1f}mm",
            "seasonal_precipitation": _window_text(stats, "season", values["season"] or 0.0),
            "yearly_precipitation": _window_text(stats, "year", values["year"] or 0.0),
        }

    @app.post("/daily_precipitation")
    def daily_precipitation(p: Point) -> dict:
        stats = data.stats()
        newest = date.fromisoformat(stats["newest_day"])
        # The 7 days straddle two stacks when newest is Sep 1 .. 6.
        series = data.series_for_years(stats["crop_years"][-2:], p.lon, p.lat)
        days = [newest - timedelta(days=i) for i in range(7)]
        out = {d.isoformat(): {"precip": round(series[d], 2)} for d in days if d in series}
        if not out:
            raise no_data()
        return out

    def _comparison(p: Point, kind: str) -> dict:
        stats = data.stats()
        newest = date.fromisoformat(stats["newest_day"])
        current_cy = stats["crop_years"][-1]
        if kind == "season":
            current = int(stats["layers"]["season"]["start"][:4])
            years = list(range(current - YEARS_SHOWN + 1, current + 1))
            stacks = list(range(years[0], current_cy + 1))  # season Y spans stacks Y and Y+1
            window, months = season_window, None
        else:
            years = list(range(current_cy - YEARS_SHOWN + 1, current_cy + 1))
            stacks = years
            window, months = crop_year_window, APRIL_TO_NOVEMBER
        series = data.series_for_years(stacks, p.lon, p.lat)
        if not series:
            raise no_data()
        return {"data": comparison_rows(series, years, window, newest, months)}

    @app.post("/season_comparison")
    def season_comparison(p: Point) -> dict:
        return _comparison(p, "season")

    @app.post("/year_comparison")
    def year_comparison(p: Point) -> dict:
        return _comparison(p, "year")

    return app


app = create_app(settings_from_env())
