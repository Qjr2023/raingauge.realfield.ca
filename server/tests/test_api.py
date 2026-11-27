import json
import shutil

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


def test_daily_precipitation(client):
    r = client.post("/daily_precipitation", json=_body(TARGET))
    assert r.status_code == 200
    data = r.json()
    assert list(data) == [
        "2026-11-25", "2026-11-24", "2026-11-23", "2026-11-22",
        "2026-11-21", "2026-11-20", "2026-11-19",
    ]
    assert data["2026-11-25"] == {"precip": 1.0}
    assert client.post("/daily_precipitation", json=_body(OUTSIDE)).status_code == 404


def test_daily_precipitation_spans_crop_year_boundary(rain_dir, tmp_path):
    # newest Sep 3 2026: Aug 28 .. 31 come from stack 2026 (2 mm), Sep 1 .. 3 from stack 2027 (1 mm)
    d = tmp_path / "rain"
    shutil.copytree(rain_dir, d)
    stats = json.loads((d / "rain_stats.json").read_text())
    stats["newest_day"] = "2026-09-03"
    (d / "rain_stats.json").write_text(json.dumps(stats))
    app = create_app(Settings(rain_dir=d, public_base="/", app_version="1.1.0"))
    r = TestClient(app).post("/daily_precipitation", json=_body(TARGET))
    assert r.status_code == 200
    assert r.json() == {
        "2026-09-03": {"precip": 1.0}, "2026-09-02": {"precip": 1.0}, "2026-09-01": {"precip": 1.0},
        "2026-08-31": {"precip": 2.0}, "2026-08-30": {"precip": 2.0},
        "2026-08-29": {"precip": 2.0}, "2026-08-28": {"precip": 2.0},
    }


def test_season_comparison(client):
    r = client.post("/season_comparison", json=_body(TARGET))
    assert r.status_code == 200
    rows = r.json()["data"]
    assert [x["year"] for x in rows] == [2020, 2021, 2022, 2023, 2024, 2025, 2026]
    by = {x["year"]: x for x in rows}
    assert by[2020] == {"year": 2020, "precip_sum": 0.0, "precip_sum_to_now": 0.0}
    # season 2025: Apr-Aug 2025 at 3 mm (153 days) in stack 2025
    # + Sep-Oct 2025 at 2 mm (61 days) in stack 2026
    assert by[2025] == {"year": 2025, "precip_sum": 581.0, "precip_sum_to_now": 581.0}
    # season 2026: Apr-Aug 2026 at 2 mm + Sep-Oct 2026 at 1 mm
    assert by[2026] == {"year": 2026, "precip_sum": 367.0, "precip_sum_to_now": 367.0}


def test_year_comparison_is_april_to_november_only(client):
    r = client.post("/year_comparison", json=_body(TARGET))
    assert r.status_code == 200
    by = {x["year"]: x for x in r.json()["data"]}
    assert sorted(by) == [2021, 2022, 2023, 2024, 2025, 2026, 2027]
    # crop year 2026: Sep-Nov 2025 (91 days) + Apr-Aug 2026 (153 days), all 2 mm;
    # to now = Sep 1 .. Nov 25 2025
    assert by[2026] == {"year": 2026, "precip_sum": 488.0, "precip_sum_to_now": 172.0}
    # crop year 2027: Sep 1 .. Nov 25 2026 at 1 mm
    assert by[2027] == {"year": 2027, "precip_sum": 86.0, "precip_sum_to_now": 86.0}


def test_legend_info_and_png(client):
    r = client.get("/legend_info")
    assert r.status_code == 200
    weekly = r.json()["weeklyRain"]
    assert weekly["uri"] == "/raingauge/api/legend/weeklyRain.png"
    assert weekly["label"] == "Last 7 days"
    assert weekly["range"] == [0.0, 25.0]
    assert "resampling=bilinear&rescale=0,25&colormap=" in weekly["tiles"]
    png = client.get("/legend/weeklyRain.png")
    assert png.status_code == 200
    assert png.headers["content-type"] == "image/png"
    assert client.get("/legend/nope.png").status_code == 404


def test_version(client):
    v = client.get("/version").json()
    assert v["web"]["minimumRequiredVersion"] == "1.1.0"
    assert "android" in v
    assert "ios" in v


def test_data_unavailable_is_503(tmp_path):
    app = create_app(Settings(rain_dir=tmp_path, public_base="/", app_version="1.1.0"))
    c = TestClient(app)
    assert c.get("/legend_info").status_code == 503
    assert c.post("/precipitation_values", json=_body(TARGET)).status_code == 503
