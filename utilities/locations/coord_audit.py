#!/usr/bin/env python3
"""
Coordinate audit (#314): suggest corrections to location coordinates and
elevations from a public elevation model and from real-world analogs.

The tool shows evidence; the GM decides per row. There is no global rule and no
auto-fix. Nothing is written until an annotated report is passed back in.

    venv/bin/python utilities/locations/coord_audit.py
    venv/bin/python utilities/locations/coord_audit.py --apply <annotated file> --dry-run
    venv/bin/python utilities/locations/coord_audit.py --apply <annotated file> [--confirm-canon]

Report mode writes a ranked table to world/data/coord-audit/ (gitignored) as
Markdown and CSV with the same rows and a blank `decision` column. Fill it in
with one of:

    move         write the suggested position to `location:` (and the confirmed
                 analog's `wikidata:` id)
    elevation    write the DEM value to `elevation:` (and `wikidata:`)
    intentional  the placement is deliberate: stamp `coord_review: intentional`
                 so the row is never suggested again
    skip         write nothing; the row is listed again next time (blank = skip)

Data
    Elevation  AWS Terrain Tiles (terrarium), credit USGS and others. Fetched
               tile by tile and cached under world/data/coord-audit/.cache/.
               MapTiler's terms do not allow scripted bulk use, so it is not
               fetched from here.
    Analogs    Wikidata P625 (CC0), looked up from `real_world_name` or an exact
               `wikidata:` id, with a descriptive User-Agent. Throttled and cached.

How rows are judged (thresholds are module constants)
    A coarse zoom-10 sample screens every location. A location whose `elevation:`
    field disagrees with the DEM by more than ELEV_TOL_M is re-sampled at zoom 12
    together with the min/max relief within RELIEF_RADIUS_KM. An analog counts as
    "far" from DIST_KM.

      resolution-suspect  the field falls inside the local relief range: the
                          point sample is probably a resolution artefact. No
                          elevation is suggested.
      coord-suspect       the analog is far and the elevation field fits it
                          better than the current position, or the analog is far
                          and elevation cannot separate the two.
      elevation-suspect   the analog sits near the current position (it
                          corroborates the coordinates) but the elevation field
                          disagrees with the DEM.
      ambiguous           the evidence disagrees with itself, or only the DEM is
                          available and it disagrees with the field.

    Rows are ranked by how many thresholds the evidence exceeds, weighted by how
    much independent evidence supports the class (RANK_WEIGHT).
"""

from __future__ import annotations

import argparse
import csv
import datetime
import difflib
import hashlib
import io
import json
import math
import os
import re
import sys
import time
from pathlib import Path

VAULT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(VAULT_ROOT / "utilities"))

from locations import location_parser  # noqa: E402
from shared.route_visibility import MATCH_KM  # noqa: E402
from shared.travel_time import _haversine_km  # noqa: E402

DEFAULT_LOCATIONS_DIR = VAULT_ROOT / "world" / "locations"
DEFAULT_ROUTES_PATH = VAULT_ROOT / "world" / "data" / "tarim-shaiel-routes.geojson"
DEFAULT_OUT_DIR = VAULT_ROOT / "world" / "data" / "coord-audit"

TILE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = ("TarimShaielCampaignTools/1.0 "
              "(https://github.com/mofro/tarim-shaiel-campaign-frame)")

COARSE_ZOOM = 10
FINE_ZOOM = 12
ELEV_TOL_M = 250            # field vs DEM disagreement worth looking at
DIST_KM = 20                # analog this far away is worth looking at
RELIEF_RADIUS_KM = 1.0      # window used to tell a resolution artefact from a real miss
RELIEF_MARGIN_M = 50
MAX_TILE_FETCHES = 600
TILE_THROTTLE_S = 0.15
WIKIDATA_THROTTLE_S = 0.3
WIKIDATA_BATCH = 50
AMBIGUOUS_KM = 100          # other in-region hits farther than this make the analog ambiguous
# lon/lat box of the Silk Road map; same-name places outside it are other places
MAP_BOX = (45.0, 15.0, 125.0, 55.0)

DECISIONS = ("move", "elevation", "intentional", "skip")
CLASSES = ("coord-suspect", "elevation-suspect", "ambiguous", "resolution-suspect")
RANK_WEIGHT = {
    "coord-suspect": 1.0,        # scaled down when the analog is the only evidence
    "elevation-suspect": 1.0,
    "ambiguous": 0.75,
    "resolution-suspect": 0.5,
}
ANALOG_ONLY_WEIGHT = 0.5

COLUMNS = [
    "rank", "slug", "class", "status", "lock", "lat", "lon",
    "analog", "analog_lat", "analog_lon", "km",
    "elev_field", "dem_here", "relief_min", "relief_max", "dem_analog",
    "suggest_lat", "suggest_lon", "suggest_elev", "wikidata", "note", "decision",
]


class AuditError(Exception):
    """A problem the GM has to fix (bad decision file, stale row, canon gate)."""


# ---------------------------------------------------------------------------
# Elevation tiles
# ---------------------------------------------------------------------------

def pixel_xy(lat: float, lon: float, z: int) -> tuple[float, float]:
    """Global Web-Mercator pixel coordinates of a point at zoom z (256 px tiles)."""
    n = 256 * 2 ** z
    px = (lon + 180.0) / 360.0 * n
    py = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return px, py


def metres_per_pixel(lat: float, z: int) -> float:
    return 156543.03392 * math.cos(math.radians(lat)) / 2 ** z


def decode_terrarium(r: int, g: int, b: int) -> float:
    return r * 256 + g + b / 256.0 - 32768.0


class BudgetExceeded(AuditError):
    pass


class TileStore:
    """Terrarium tiles from a disk cache, fetching what is missing.

    `fetch(url) -> bytes | None` is injectable so tests never touch the network.
    A tile that cannot be had (404, network failure) reads as no data.
    """

    def __init__(self, cache_dir: Path, *, offline: bool = False, fetch=None,
                 max_fetches: int = MAX_TILE_FETCHES, sleep=time.sleep):
        self.cache_dir = Path(cache_dir) / "terrarium"
        self.offline = offline
        self._fetch = fetch or _http_get_bytes
        self.max_fetches = max_fetches
        self._sleep = sleep
        self._images: dict = {}
        self.fetched = 0
        self.cached = 0
        self.missing = 0

    def _tile_path(self, z: int, x: int, y: int) -> Path:
        return self.cache_dir / str(z) / str(x) / f"{y}.png"

    def _pixels(self, z: int, x: int, y: int):
        key = (z, x, y)
        if key in self._images:
            return self._images[key]
        from PIL import Image  # lazy: only the audit needs Pillow

        path = self._tile_path(z, x, y)
        data = None
        if path.exists():
            data = path.read_bytes()
            self.cached += 1
        elif not self.offline:
            if self.fetched >= self.max_fetches:
                raise BudgetExceeded(
                    f"more than {self.max_fetches} tile downloads needed; "
                    "raise --max-tiles if that is intended")
            data = self._fetch(TILE_URL.format(z=z, x=x, y=y))
            self.fetched += 1
            self._sleep(TILE_THROTTLE_S)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data or b"")
        pixels = None
        if data:
            pixels = Image.open(io.BytesIO(data)).convert("RGB").load()
        else:
            self.missing += 1
        self._images[key] = pixels
        return pixels

    def elevation_at_pixel(self, z: int, gx: int, gy: int) -> float | None:
        pixels = self._pixels(z, gx // 256, gy // 256)
        if pixels is None:
            return None
        return decode_terrarium(*pixels[gx % 256, gy % 256])

    def elevation(self, lat: float, lon: float, z: int) -> float | None:
        px, py = pixel_xy(lat, lon, z)
        return self.elevation_at_pixel(z, int(px), int(py))

    def relief(self, lat: float, lon: float, z: int,
               radius_km: float = RELIEF_RADIUS_KM) -> tuple[float, float] | None:
        """(min, max) elevation in a square window around the point."""
        px, py = pixel_xy(lat, lon, z)
        r = max(1, math.ceil(radius_km * 1000.0 / metres_per_pixel(lat, z)))
        values = []
        for gy in range(int(py) - r, int(py) + r + 1):
            for gx in range(int(px) - r, int(px) + r + 1):
                v = self.elevation_at_pixel(z, gx, gy)
                if v is not None:
                    values.append(v)
        return (min(values), max(values)) if values else None


def _http_get_bytes(url: str) -> bytes | None:
    """The body, or None for a tile that does not exist. A failed request raises
    instead, so a network blip is never cached as "no tile"."""
    import requests

    last = None
    for _ in range(3):
        try:
            resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
        except requests.RequestException as exc:
            last = str(exc)
        else:
            if resp.status_code == 200:
                return resp.content
            if resp.status_code in (403, 404):
                return None
            last = f"HTTP {resp.status_code}"
        time.sleep(1.0)
    raise AuditError(f"tile request failed ({last}): {url}")


def _http_get_json(params: dict) -> dict:
    import requests

    params = {**params, "format": "json"}
    last = None
    for _ in range(3):
        try:
            resp = requests.get(WIKIDATA_API, params=params,
                                headers={"User-Agent": USER_AGENT}, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            last = f"HTTP {resp.status_code}"
        except requests.RequestException as exc:
            last = str(exc)
        time.sleep(1.0)
    raise AuditError(f"Wikidata request failed: {last}")


# ---------------------------------------------------------------------------
# Wikidata analogs
# ---------------------------------------------------------------------------

def in_map_box(lat: float, lon: float) -> bool:
    west, south, east, north = MAP_BOX
    return west <= lon <= east and south <= lat <= north


def _slug_key(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "x"
    return f"{base}-{hashlib.sha1(text.lower().encode('utf-8')).hexdigest()[:8]}"


def _compact_entity(qid: str, raw: dict) -> dict:
    claims = raw.get("claims") or {}
    coord = None
    for claim in claims.get("P625") or []:
        value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value")
        if value and "latitude" in value and "longitude" in value:
            coord = [float(value["latitude"]), float(value["longitude"])]
            break
    instance_of = []
    for claim in claims.get("P31") or []:
        value = ((claim.get("mainsnak") or {}).get("datavalue") or {}).get("value")
        if isinstance(value, dict) and value.get("id"):
            instance_of.append(value["id"])
    return {
        "qid": qid,
        "label": ((raw.get("labels") or {}).get("en") or {}).get("value", qid),
        "description": ((raw.get("descriptions") or {}).get("en") or {}).get("value", ""),
        "coord": coord,
        "instance_of": instance_of,
    }


class Wikidata:
    """Place lookups by name or exact id, cached on disk.

    `get_json(params) -> dict` is injectable for tests.
    """

    def __init__(self, cache_dir: Path, *, offline: bool = False, get_json=None,
                 sleep=time.sleep):
        self.dir = Path(cache_dir) / "wikidata"
        self.offline = offline
        self._get = get_json or _http_get_json
        self._sleep = sleep
        self.requests = 0

    def _read(self, path: Path):
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def _write(self, path: Path, data) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def _search_path(self, name: str) -> Path:
        return self.dir / "search" / f"{_slug_key(name)}.json"

    def _entity_path(self, qid: str) -> Path:
        return self.dir / "entities" / f"{qid}.json"

    def search(self, name: str) -> list[dict]:
        path = self._search_path(name)
        cached = self._read(path)
        if cached is not None:
            return cached
        if self.offline:
            return []
        data = self._get({"action": "wbsearchentities", "search": name,
                          "language": "en", "uselang": "en", "type": "item", "limit": 3})
        self.requests += 1
        self._sleep(WIKIDATA_THROTTLE_S)
        hits = [{"id": h["id"], "label": h.get("label", ""),
                 "description": h.get("description", "")}
                for h in data.get("search", [])]
        self._write(path, hits)
        return hits

    def fetch_entities(self, qids: list[str]) -> None:
        todo = [q for q in dict.fromkeys(qids) if not self._entity_path(q).exists()]
        if self.offline:
            return
        for i in range(0, len(todo), WIKIDATA_BATCH):
            chunk = todo[i:i + WIKIDATA_BATCH]
            data = self._get({"action": "wbgetentities", "ids": "|".join(chunk),
                              "props": "labels|descriptions|claims", "languages": "en"})
            self.requests += 1
            self._sleep(WIKIDATA_THROTTLE_S)
            for qid in chunk:
                raw = (data.get("entities") or {}).get(qid) or {}
                self._write(self._entity_path(qid), _compact_entity(qid, raw))

    def entity(self, qid: str) -> dict | None:
        return self._read(self._entity_path(qid))

    def prefetch(self, names: list[str], qids: list[str]) -> None:
        """Search every name, then fetch all needed entities in batches."""
        wanted = list(qids)
        for name in dict.fromkeys(names):
            wanted += [h["id"] for h in self.search(name)]
        self.fetch_entities(wanted)

    def analog(self, name: str | None, qid: str | None = None) -> dict | None:
        """{qid,label,description,lat,lon,ambiguous,...} or None.

        An exact `qid` is trusted. Otherwise the first search hit that has
        coordinates inside the map's region is taken, and flagged ambiguous when
        another such hit lies more than AMBIGUOUS_KM away.
        """
        if qid:
            ent = self.entity(qid)
            if ent and ent["coord"]:
                return _analog(ent, ambiguous=False, exact=True)
            return None
        if not name:
            return None
        found = []
        for hit in self.search(name):
            ent = self.entity(hit["id"])
            if ent and ent["coord"] and in_map_box(*ent["coord"]):
                found.append(ent)
        if not found:
            return None
        first = found[0]
        ambiguous = any(
            _haversine_km(first["coord"][1], first["coord"][0], e["coord"][1], e["coord"][0])
            > AMBIGUOUS_KM for e in found[1:])
        return _analog(first, ambiguous=ambiguous, exact=False)


def _analog(ent: dict, *, ambiguous: bool, exact: bool) -> dict:
    return {"qid": ent["qid"], "label": ent["label"], "description": ent["description"],
            "lat": ent["coord"][0], "lon": ent["coord"][1],
            "ambiguous": ambiguous, "exact": exact}


# ---------------------------------------------------------------------------
# Locations
# ---------------------------------------------------------------------------

def load_locations(locations_dir: Path) -> tuple[list[dict], int]:
    """(rows with coordinates, count of locations without any). Skips `_`/`zz` files."""
    rows, no_coords = [], 0
    for path in sorted(Path(locations_dir).glob("*.md")):
        data = location_parser.parse_location(path)
        if data is None:
            continue
        if data["lat"] is None or data["lon"] is None:
            no_coords += 1
            continue
        fm, _ = location_parser._parse_fm(path.read_text(encoding="utf-8"))
        raw_elev = fm.get("elevation")
        try:
            elev = int(raw_elev) if raw_elev is not None else None
        except (TypeError, ValueError):
            elev = None
        real = str(fm.get("real_world_name") or "").strip()
        rows.append({
            "slug": data["slug"],
            "path": path,
            "name": data["title"],
            "status": data["status"],
            "lat": data["lat"],
            "lon": data["lon"],
            "elev": elev,
            "real_world_name": "" if real.lower() == "redirect" else real,
            "wikidata": str(fm.get("wikidata") or "").strip(),
            "reviewed": str(fm.get("coord_review") or "").strip().lower() == "intentional",
        })
    return rows, no_coords


# ---------------------------------------------------------------------------
# Judging
# ---------------------------------------------------------------------------

def elevation_fit(field: int | None, dem: float | None,
                  relief: tuple[float, float] | None = None) -> str | None:
    """'point' | 'relief' | 'miss', or None when it cannot be judged."""
    if field is None or dem is None:
        return None
    if abs(field - dem) <= ELEV_TOL_M:
        return "point"
    if relief and relief[0] - RELIEF_MARGIN_M <= field <= relief[1] + RELIEF_MARGIN_M:
        return "relief"
    return "miss"


def classify(field: int | None, dem_here: float | None,
             relief: tuple[float, float] | None,
             analog_km: float | None, dem_analog: float | None) -> str | None:
    """Class name, or None when the evidence is consistent."""
    here = elevation_fit(field, dem_here, relief)
    far = analog_km is not None and analog_km >= DIST_KM
    if far:
        there = elevation_fit(field, dem_analog)
        here_ok = here in ("point", "relief")
        there_ok = there == "point"
        if here is not None and there is not None:
            if there_ok and not here_ok:
                return "coord-suspect"
            if here_ok != there_ok or (not here_ok and not there_ok):
                return "ambiguous"
        return "coord-suspect"   # elevation cannot separate the two positions
    if here in (None, "point"):
        return None
    if here == "relief":
        return "resolution-suspect"
    return "elevation-suspect" if analog_km is not None else "ambiguous"


def score(cls: str, field: int | None, dem_here: float | None,
          analog_km: float | None, analog_only: bool) -> float:
    """Multiples of the thresholds the evidence exceeds, weighted by its strength."""
    gap = abs(field - dem_here) / ELEV_TOL_M if field is not None and dem_here is not None else 0.0
    dist = analog_km / DIST_KM if analog_km is not None else 0.0
    weight = RANK_WEIGHT[cls] * (ANALOG_ONLY_WEIGHT if analog_only else 1.0)
    return round(max(gap, dist) * weight, 2)


def _m(value) -> str:
    return "?" if value is None else f"{value:.0f} m"


def _fmt(degrees: float) -> str:
    """A coordinate with up to 6 decimals, no trailing zeros."""
    return f"{degrees:.6f}".rstrip("0").rstrip(".")


def build_rows(locs: list[dict], tiles: TileStore, wikidata: Wikidata) -> tuple[list[dict], dict]:
    """Judge every location; returns (ranked listed rows, summary counts)."""
    open_locs = [l for l in locs if not l["reviewed"]]
    wikidata.prefetch([l["real_world_name"] for l in open_locs
                       if l["real_world_name"] and not l["wikidata"]],
                      [l["wikidata"] for l in open_locs if l["wikidata"]])
    listed, counts = [], {"checked": 0, "consistent": 0, "reviewed": 0}
    for loc in locs:
        if loc["reviewed"]:
            counts["reviewed"] += 1
            continue
        counts["checked"] += 1
        analog = wikidata.analog(loc["real_world_name"], loc["wikidata"] or None)
        km = dem_analog = None
        if analog:
            km = _haversine_km(loc["lon"], loc["lat"], analog["lon"], analog["lat"])
            dem_analog = tiles.elevation(analog["lat"], analog["lon"], COARSE_ZOOM)
        dem_here = tiles.elevation(loc["lat"], loc["lon"], COARSE_ZOOM)
        relief = None
        if (loc["elev"] is not None and dem_here is not None
                and abs(loc["elev"] - dem_here) > ELEV_TOL_M):
            fine = tiles.elevation(loc["lat"], loc["lon"], FINE_ZOOM)
            if fine is not None:
                dem_here = fine
            relief = tiles.relief(loc["lat"], loc["lon"], FINE_ZOOM)
        cls = classify(loc["elev"], dem_here, relief, km, dem_analog)
        if cls is None:
            counts["consistent"] += 1
            continue
        analog_only = cls == "coord-suspect" and (
            elevation_fit(loc["elev"], dem_here, relief) is None
            or elevation_fit(loc["elev"], dem_analog) is None)
        listed.append(_row(loc, cls, analog, km, dem_here, relief, dem_analog, analog_only))
    listed.sort(key=lambda r: (-r["_score"], r["slug"]))
    for i, row in enumerate(listed, 1):
        row["rank"] = i
    return listed, counts


def _row(loc, cls, analog, km, dem_here, relief, dem_analog, analog_only) -> dict:
    field = loc["elev"]
    suggest_pos = analog is not None and km is not None and km >= DIST_KM
    miss = elevation_fit(field, dem_here, relief) == "miss"
    suggest_elev = round(dem_here) if (miss and dem_here is not None
                                       and cls in ("elevation-suspect", "ambiguous")) else None
    bits = []
    if field is not None:
        bits.append(f"elevation field {_m(field)} vs DEM {_m(dem_here)} here")
        if relief and cls == "resolution-suspect":
            bits.append(f"field is inside the {_m(relief[0])}–{_m(relief[1])} relief within "
                        f"{RELIEF_RADIUS_KM:g} km")
    else:
        bits.append(f"no elevation field; DEM {_m(dem_here)} here")
    if analog:
        tail = f"{analog['label']}" + (f" ({analog['description']})" if analog["description"] else "")
        bits.append(f"analog {tail} is {km:.0f} km away, DEM {_m(dem_analog)}")
        if analog["ambiguous"]:
            bits.append("other same-name places exist: confirm this is the right one")
    elif loc["real_world_name"]:
        bits.append(f"no Wikidata analog found for “{loc['real_world_name']}”")
    else:
        bits.append("no real_world_name: DEM-only, review by hand")
    if analog_only:
        bits.append("analog is the only evidence")
    return {
        "_score": score(cls, field, dem_here, km, analog_only),
        "rank": 0,
        "slug": loc["slug"],
        "class": cls,
        "status": loc["status"],
        "lock": "🔒" if loc["status"] == "canon" else "",
        "lat": _fmt(loc["lat"]),
        "lon": _fmt(loc["lon"]),
        "analog": (analog["label"] if analog else ""),
        "analog_lat": (f"{analog['lat']:.4f}" if analog else ""),
        "analog_lon": (f"{analog['lon']:.4f}" if analog else ""),
        "km": (f"{km:.0f}" if km is not None else ""),
        "elev_field": ("" if field is None else str(field)),
        "dem_here": ("" if dem_here is None else f"{dem_here:.0f}"),
        "relief_min": ("" if not relief else f"{relief[0]:.0f}"),
        "relief_max": ("" if not relief else f"{relief[1]:.0f}"),
        "dem_analog": ("" if dem_analog is None else f"{dem_analog:.0f}"),
        "suggest_lat": (f"{analog['lat']:.4f}" if suggest_pos else ""),
        "suggest_lon": (f"{analog['lon']:.4f}" if suggest_pos else ""),
        "suggest_elev": ("" if suggest_elev is None else str(suggest_elev)),
        "wikidata": (analog["qid"] if analog else ""),
        "note": "; ".join(bits),
        "decision": "",
    }


# ---------------------------------------------------------------------------
# Report files
# ---------------------------------------------------------------------------

def _md_cell(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(rows: list[dict], stamp: str) -> str:
    out = [
        f"# Coordinate audit {stamp}",
        "",
        "Fill the `decision` column with `move`, `elevation`, `intentional` or `skip` "
        "(blank = skip), then run `coord_audit.py --apply <this file> --dry-run`. "
        "🔒 marks a canon file: applying to it needs `--confirm-canon`.",
        "",
        "| " + " | ".join(COLUMNS) + " |",
        "|" + "|".join("---" for _ in COLUMNS) + "|",
    ]
    for row in rows:
        out.append("| " + " | ".join(_md_cell(row[c]) for c in COLUMNS) + " |")
    return "\n".join(out) + "\n"


def render_csv(rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLUMNS, extrasaction="ignore", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


def write_report(rows: list[dict], out_dir: Path, now: datetime.datetime) -> tuple[Path, Path]:
    """Write the .md and .csv; never overwrites an earlier (maybe annotated) report."""
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = now.strftime("%Y-%m-%dT%H%M%S")
    md, csv_path = out_dir / f"audit-{stamp}.md", out_dir / f"audit-{stamp}.csv"
    n = 1
    while md.exists() or csv_path.exists():
        n += 1
        md, csv_path = out_dir / f"audit-{stamp}-{n}.md", out_dir / f"audit-{stamp}-{n}.csv"
    md.write_text(render_markdown(rows, stamp), encoding="utf-8")
    csv_path.write_text(render_csv(rows), encoding="utf-8")
    return md, csv_path


# ---------------------------------------------------------------------------
# Reading decisions back
# ---------------------------------------------------------------------------

_UNESCAPED_PIPE = re.compile(r"(?<!\\)\|")


def _md_cells(line: str) -> list[str]:
    inner = line.strip()
    if inner.startswith("|"):
        inner = inner[1:]
    if inner.endswith("|") and not inner.endswith("\\|"):
        inner = inner[:-1]
    return [c.strip().replace("\\|", "|") for c in _UNESCAPED_PIPE.split(inner)]


def read_decisions(path: Path) -> list[dict]:
    """Rows of an annotated report, as dicts keyed by column name."""
    text = Path(path).read_text(encoding="utf-8-sig")
    if str(path).lower().endswith(".csv"):
        return [dict(r) for r in csv.DictReader(io.StringIO(text))]
    header, rows = None, []
    for line in text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = _md_cells(line)
        if header is None:
            if "slug" in cells and "decision" in cells:
                header = cells
            continue
        if all(set(c) <= set("-: ") for c in cells):
            continue
        rows.append(dict(zip(header, cells)))
    if header is None:
        raise AuditError(f"{path}: no table with `slug` and `decision` columns found")
    return rows


# ---------------------------------------------------------------------------
# Applying decisions
# ---------------------------------------------------------------------------

def _num(row: dict, key: str, what: str) -> float:
    try:
        return float(str(row.get(key, "")).strip())
    except ValueError:
        raise AuditError(f"{row.get('slug')}: `{key}` must be a number to {what}") from None


def plan_changes(rows: list[dict], locations_dir: Path, *, confirm_canon: bool,
                 today: str) -> tuple[list[dict], int, list[str]]:
    """Validate every decided row; return (changes, skipped, errors). Writes nothing."""
    import devserver  # the same frontmatter edit path as the Workshop's coordinate PUT

    changes, skipped, errors = [], 0, []
    seen = set()
    for row in rows:
        slug = str(row.get("slug", "")).strip()
        decision = str(row.get("decision", "")).strip().lower()
        if decision in ("", "skip"):
            skipped += 1
            continue
        try:
            if decision not in DECISIONS:
                raise AuditError(f"{slug}: unknown decision “{decision}” "
                                 f"(use {', '.join(DECISIONS)})")
            if slug in seen:
                raise AuditError(f"{slug}: appears more than once with a decision")
            seen.add(slug)
            path = Path(locations_dir) / f"{slug}.md"
            if not path.exists():
                raise AuditError(f"{slug}: no such location file")
            old = path.read_text(encoding="utf-8")
            fm, _ = location_parser._parse_fm(old)
            loc = fm.get("location")
            try:
                f_lat, f_lon = float(loc[0]), float(loc[1])
            except (TypeError, ValueError, IndexError):
                raise AuditError(f"{slug}: file has no coordinates") from None
            if (abs(f_lat - _num(row, "lat", "check the row")) > 1e-4
                    or abs(f_lon - _num(row, "lon", "check the row")) > 1e-4):
                raise AuditError(f"{slug}: stale row — the file's coordinates changed since the "
                                 "report was made; re-run the audit")
            f_elev = fm.get("elevation")
            row_elev = str(row.get("elev_field", "")).strip()
            if (str(f_elev) if f_elev is not None else "") != row_elev:
                raise AuditError(f"{slug}: stale row — the file's elevation changed since the "
                                 "report was made; re-run the audit")
            if str(fm.get("status", "")).strip().lower() == "canon" and not confirm_canon:
                raise AuditError(f"{slug}: canon file — re-run with --confirm-canon to change it")

            fields: dict = {}
            new = old
            qid = str(row.get("wikidata", "")).strip()
            if decision == "move":
                lat = round(_num(row, "suggest_lat", "move"), 4)
                lon = round(_num(row, "suggest_lon", "move"), 4)
                new = devserver._set_location(new, lat, lon)
                if qid:
                    fields["wikidata"] = qid
            elif decision == "elevation":
                fields["elevation"] = int(round(_num(row, "suggest_elev", "set the elevation")))
                # only confirm an analog that corroborates the current position
                km = str(row.get("km", "")).strip()
                if qid and km and _num(row, "km", "check the analog") < DIST_KM:
                    fields["wikidata"] = qid
            else:  # intentional
                fields["coord_review"] = "intentional"
                fields["coord_reviewed"] = today
            new = devserver._set_frontmatter_fields(new, fields)   # also bumps last_updated
            changes.append({"slug": slug, "decision": decision, "path": path, "old": old,
                            "new": new, "old_lat": f_lat, "old_lon": f_lon})
        except AuditError as exc:
            errors.append(str(exc))
    return changes, skipped, errors


def routes_touching(routes_path: Path, lat: float, lon: float) -> list[str]:
    """Ids of routes whose first or last point sits within MATCH_KM of a position."""
    try:
        gj = json.loads(Path(routes_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    hits = []
    for feat in gj.get("features", []):
        coords = (feat.get("geometry") or {}).get("coordinates") or []
        if len(coords) < 2:
            continue
        for end in (coords[0], coords[-1]):
            if _haversine_km(end[0], end[1], lon, lat) <= MATCH_KM:
                hits.append(str(feat.get("id")))
                break
    return hits


def diff_text(change: dict, base: Path) -> str:
    try:
        rel = change["path"].relative_to(base)
    except ValueError:
        rel = change["path"].name
    return "".join(difflib.unified_diff(
        change["old"].splitlines(keepends=True), change["new"].splitlines(keepends=True),
        fromfile=f"a/{rel}", tofile=f"b/{rel}", n=1))


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def apply_decisions(decision_file: Path, locations_dir: Path, routes_path: Path, *,
                    dry_run: bool, confirm_canon: bool, out=print) -> int:
    """Print the diff per decided row and write it unless dry_run. 0 ok, 2 on any error."""
    rows = read_decisions(decision_file)
    today = datetime.date.today().isoformat()
    changes, skipped, errors = plan_changes(rows, locations_dir, confirm_canon=confirm_canon,
                                            today=today)
    if errors:
        out("Nothing was written. Fix these rows and run again:")
        for e in errors:
            out(f"  - {e}")
        return 2
    base = Path(locations_dir).parent.parent
    for ch in changes:
        out(diff_text(ch, base).rstrip("\n"))
    if not dry_run:
        for ch in changes:
            write_atomic(ch["path"], ch["new"])
    verb = "would change" if dry_run else "changed"
    out(f"\n{verb} {len(changes)} file(s); {skipped} row(s) skipped (blank or skip).")
    for ch in changes:
        if ch["decision"] != "move":
            continue
        ids = routes_touching(routes_path, ch["old_lat"], ch["old_lon"])
        if ids:
            out(f"{ch['slug']} moved: Regenerate these routes in the Workshop so they follow it: "
                + ", ".join(ids))
    if changes and not dry_run:
        out("Rebuild next: venv/bin/python utilities/build.py all --gm")
    return 0


# ---------------------------------------------------------------------------
# Command line
# ---------------------------------------------------------------------------

def run_report(args) -> int:
    out_dir = Path(args.out_dir)
    cache = out_dir / ".cache"
    locs, no_coords = load_locations(Path(args.locations_dir))
    tiles = TileStore(cache, offline=args.offline, max_fetches=args.max_tiles)
    wikidata = Wikidata(cache, offline=args.offline)
    try:
        rows, counts = build_rows(locs, tiles, wikidata)
    except BudgetExceeded as exc:
        print(f"Stopped: {exc}", file=sys.stderr)
        return 2
    md, csv_path = write_report(rows, out_dir, datetime.datetime.now())
    print(f"{counts['checked']} locations checked ({no_coords} have no coordinates, "
          f"{counts['reviewed']} marked intentional): {len(rows)} listed, "
          f"{counts['consistent']} consistent.")
    print(f"Tiles: {tiles.fetched} downloaded, {tiles.cached} from cache, {tiles.missing} missing. "
          f"Wikidata requests: {wikidata.requests}.")
    for row in rows[:args.top]:
        print(f"{row['rank']:>3}  {row['_score']:>6}  "
              f"{row['class']:<19} {row['slug']:<26} {row['note']}")
    print(f"\nReport: {md}\n        {csv_path}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--apply", metavar="FILE", help="annotated report (.csv or .md) to apply")
    ap.add_argument("--dry-run", action="store_true", help="with --apply: print the diffs, write nothing")
    ap.add_argument("--confirm-canon", action="store_true",
                    help="with --apply: allow changes to files marked status: canon")
    ap.add_argument("--locations-dir", default=str(DEFAULT_LOCATIONS_DIR))
    ap.add_argument("--routes", default=str(DEFAULT_ROUTES_PATH))
    ap.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--offline", action="store_true", help="use cached tiles and Wikidata only")
    ap.add_argument("--max-tiles", type=int, default=MAX_TILE_FETCHES)
    ap.add_argument("--top", type=int, default=15, help="rows to print after a report run")
    args = ap.parse_args(argv)
    try:
        if args.apply:
            return apply_decisions(Path(args.apply), Path(args.locations_dir), Path(args.routes),
                                   dry_run=args.dry_run, confirm_canon=args.confirm_canon)
        return run_report(args)
    except AuditError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
