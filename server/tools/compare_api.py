"""Compare two Rain Gauge APIs at a list of points.

    python compare_api.py https://api.example.org https://server.example.org/raingauge/api

Prints, per point: the three window totals from each API, and per comparison chart the per-year
difference. Weekly totals are expected to agree to about 0.1 mm; history differs by source.
A point that one side answers with an HTTP error is reported as such and skipped.
"""
import json
import re
import sys
import urllib.error
import urllib.request

POINTS = {
    "Saskatoon": (52.13, -106.67),
    "Regina": (50.45, -104.62),
    "Swift Current": (50.29, -107.80),
    "Yorkton": (51.21, -102.46),
    "Calgary": (51.05, -114.07),
    "Winnipeg": (49.90, -97.14),
    "Lethbridge": (49.70, -112.83),
    "Prince Albert": (53.20, -105.75),
}


def post(base: str, path: str, lat: float, lon: float) -> dict:
    """POST {lat, lon} to base/path and return the JSON body."""
    req = urllib.request.Request(
        f"{base}/{path}", data=json.dumps({"lat": lat, "lon": lon}).encode(),
        headers={"Content-Type": "application/json"}, method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def mm(text: str) -> float:
    """The number before 'mm' in a precipitation_values string."""
    m = re.search(r"([\d.]+)mm", text)
    return float(m.group(1)) if m else float("nan")


def main(old: str, new: str) -> None:
    print(f"{'point':14} {'week old/new':>16} {'season old/new':>18} {'year old/new':>16}")
    for name, (lat, lon) in POINTS.items():
        try:
            a = post(old, "precipitation_values", lat, lon)
            b = post(new, "precipitation_values", lat, lon)
        except urllib.error.HTTPError as e:
            print(f"{name:14} HTTP {e.code} ({e.url})")
            continue
        print(
            f"{name:14} {mm(a['weekly_precipitation']):7.1f}/{mm(b['weekly_precipitation']):<7.1f} "
            f"{mm(a['seasonal_precipitation']):8.1f}/{mm(b['seasonal_precipitation']):<8.1f} "
            f"{mm(a['yearly_precipitation']):7.1f}/{mm(b['yearly_precipitation']):<7.1f}"
        )
    for chart in ("season_comparison", "year_comparison"):
        print(f"\n{chart}: precip_sum old -> new (difference)")
        for name, (lat, lon) in POINTS.items():
            try:
                a = {int(r["year"]): r["precip_sum"] for r in post(old, chart, lat, lon)["data"]}
                b = {int(r["year"]): r["precip_sum"] for r in post(new, chart, lat, lon)["data"]}
            except urllib.error.HTTPError as e:
                print(f"  {name:14} HTTP {e.code} ({e.url})")
                continue
            cells = [f"{y}: {a[y]:.0f}->{b[y]:.0f} ({b[y]-a[y]:+.0f})" for y in sorted(set(a) & set(b))]
            print(f"  {name:14} " + "  ".join(cells))


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(sys.argv[1].rstrip("/"), sys.argv[2].rstrip("/"))
