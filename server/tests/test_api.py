import json

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from tests.conftest import NODATA_PIXEL, OUTSIDE, TARGET


@pytest.fixture
def client(rain_dir):
    app = create_app(Settings(rain_dir=rain_dir, public_base="/raingauge/", app_version="1.1.0"))
    return TestClient(app)


def _body(p):
    return {"lat": p[1], "lon": p[0]}


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "newest_day": "2026-11-25"}


def test_precipitation_values(client):
    r = client.post("/precipitation_values", json=_body(TARGET))
    assert r.status_code == 200
    assert r.json() == {
        "weekly_precipitation": "Last 7 days: 7.0mm",
        "seasonal_precipitation": "Apr 01 - Oct 31: 214.0mm",
        "yearly_precipitation": "Sept 01 - today: 86.0mm",
    }


def test_precipitation_values_outside_is_404(client):
    for p in (OUTSIDE, NODATA_PIXEL):
        r = client.post("/precipitation_values", json=_body(p))
        assert r.status_code == 404
        assert r.json() == {"detail": "No data at this location"}


def test_bad_input_is_422(client):
    assert client.post("/precipitation_values", json={"lat": 95, "lon": -106}).status_code == 422
    assert client.post("/precipitation_values", json={"lat": 52}).status_code == 422


def test_legend_info_and_png(client):
    r = client.get("/legend_info")
    assert r.status_code == 200
    weekly = r.json()["weeklyRain"]
    assert weekly["uri"] == "/raingauge/api/legend/weeklyRain.png"
    assert weekly["label"] == "Last 7 days"
    assert weekly["range"] == [0.0, 25.0]
    assert "resampling=bilinear&rescale=0,25&colormap=" in weekly["tiles"]
    assert weekly["rain_stats"] == "/raingauge/api/rain_stats"
    png = client.get("/legend/weeklyRain.png")
    assert png.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert client.get("/legend/nope.png").status_code == 404


def test_rain_stats(client):
    r = client.get("/rain_stats")
    assert r.status_code == 200
    stats = r.json()
    assert stats["crop_years"] == [2025, 2026, 2027]
    assert stats["layers"]["season"]["start"] == "2026-04-01"


def test_version(client):
    v = client.get("/version").json()
    assert v["web"]["minimumRequiredVersion"] == "1.1.0"
    assert "android" in v
    assert "ios" in v


def test_data_unavailable_is_503(tmp_path):
    app = create_app(Settings(rain_dir=tmp_path, public_base="/", app_version="1.1.0"))
    c = TestClient(app)
    assert c.get("/legend_info").status_code == 503
    assert c.get("/rain_stats").status_code == 503
    assert c.post("/precipitation_values", json=_body(TARGET)).status_code == 503
