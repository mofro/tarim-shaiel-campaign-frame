"""
Place Fantasy Town Generator (FTG) town maps on the world map.

An FTG GeoJSON export is in local metres (no CRS, origin at the town centre, +x east,
+y north). The file stays untouched in world/maps/cities/; at Workshop build time each
town is moved to the `location:` of the page whose slug equals the file stem, turned
by that page's `town_rotation:` (degrees clockwise about `location:`), and trimmed to
what the map draws. The people file (`<Town>.json`) never rides in this geometry.

Usage (from the Workshop builder):
    towns  = build_overlays(load_all_locations(LOCATIONS_DIR))
    gm     = feature_collection(towns)
    player = feature_collection(player_towns(towns))
    index  = town_index(towns)   # Workshop only: lets the page turn a town live
"""

import json
import math
import sys
from pathlib import Path

VAULT_ROOT = Path(__file__).parent.parent.parent
CITIES_DIR = VAULT_ROOT / "world" / "maps" / "cities"

# Properties that reach the page. Everything else FTG writes is dropped.
KEPT_PROPERTIES = ("type", "id", "name", "buildingType", "edgeType")

# Edges FTG draws but the map should not: INVISIBLE is a routing helper, not a feature.
DROPPED_EDGE_TYPES = frozenset({"INVISIBLE"})

# Decimal places kept on lon/lat: 6 is about 0.1 m, finer than any FTG building edge.
COORD_DECIMALS = 6


def metres_per_degree(lat: float) -> tuple[float, float]:
    """(metres per degree of latitude, metres per degree of longitude) at `lat`.

    WGS84 series. At 36.6622 it gives 110,971.3 and 89,403.8.
    """
    phi = math.radians(lat)
    m_lat = (111132.92 - 559.82 * math.cos(2 * phi)
             + 1.175 * math.cos(4 * phi) - 0.0023 * math.cos(6 * phi))
    m_lon = (111412.84 * math.cos(phi) - 93.5 * math.cos(3 * phi)
             + 0.118 * math.cos(5 * phi))
    return m_lat, m_lon


class Georeference:
    """Local metres to [lon, lat], anchored at the town centre.

    `rotation` turns the town clockwise about the centre, in degrees, like a compass
    bearing: 90 sends the town's north to the east. It is applied to the local metres
    before the flat-earth conversion, so the shape stays rigid. 0 and 360 do not turn
    it at all.
    """

    def __init__(self, lat: float, lon: float, rotation: float = 0.0):
        self.lat = lat
        self.lon = lon
        self.rotation = rotation
        self.m_lat, self.m_lon = metres_per_degree(lat)
        turn = rotation % 360
        self._cos, self._sin = (math.cos(math.radians(turn)), math.sin(math.radians(turn))) \
            if turn else (1.0, 0.0)

    def to_lonlat(self, x: float, y: float) -> list[float]:
        x, y = x * self._cos + y * self._sin, -x * self._sin + y * self._cos
        return [round(self.lon + x / self.m_lon, COORD_DECIMALS),
                round(self.lat + y / self.m_lat, COORD_DECIMALS)]

    def to_local(self, lon: float, lat: float) -> tuple[float, float]:
        x, y = (lon - self.lon) * self.m_lon, (lat - self.lat) * self.m_lat
        return (x * self._cos - y * self._sin, x * self._sin + y * self._cos)

    def ring(self, coords: list) -> list:
        return [self.to_lonlat(x, y) for x, y in coords]


def _geometry(geom: dict, ref: Georeference) -> dict:
    if geom["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": [ref.ring(r) for r in geom["coordinates"]]}
    if geom["type"] == "LineString":
        return {"type": "LineString", "coordinates": ref.ring(geom["coordinates"])}
    raise ValueError(f"unsupported FTG geometry: {geom['type']}")


def build_town_overlay(ftg: dict, lat: float, lon: float, rotation: float = 0.0) -> list[dict]:
    """Features of one FTG town, georeferenced, turned by `rotation` and trimmed.

    BACKGROUND polygons (lawn / grass / road texture) are not drawn. INVISIBLE edges
    are dropped.
    """
    ref = Georeference(lat, lon, rotation)
    out = []
    for f in ftg["features"]:
        props = f.get("properties", {})
        kind = props.get("type")
        if kind not in ("BUILDING", "EDGE", "WATER"):
            continue
        if kind == "EDGE" and props.get("edgeType") in DROPPED_EDGE_TYPES:
            continue
        kept = {k: props[k] for k in KEPT_PROPERTIES if k in props}
        out.append({"type": "Feature", "properties": kept, "geometry": _geometry(f["geometry"], ref)})
    return out


def build_overlays(locations: list, cities_dir: Path = CITIES_DIR) -> list[dict]:
    """Every town in `cities_dir` that has a placed location page, as
    `{"slug", "visibility", "lat", "lon", "rotation", "features"}` entries. Slug and
    visibility sit on the town, not on each feature, which would add about 120 KB for
    Dehdadi. `rotation` is the page's `town_rotation:` (0 when absent).

    A `<Stem>.geojson` belongs to the location whose slug equals the stem, ignoring
    case. A town with no page, or a page without coordinates, is skipped with a
    warning on stderr; the build goes on.
    """
    by_slug = {loc["slug"].lower(): loc for loc in locations}
    towns: list[dict] = []
    for path in sorted(cities_dir.glob("*.geojson")):
        loc = by_slug.get(path.stem.lower())
        if loc is None:
            print(f"  WARN: {path.name} has no location page (slug '{path.stem.lower()}'); skipped",
                  file=sys.stderr)
            continue
        if loc["lat"] is None or loc["lon"] is None:
            print(f"  WARN: {path.name}: location '{loc['slug']}' has no coordinates; skipped",
                  file=sys.stderr)
            continue
        ftg = json.loads(path.read_text(encoding="utf-8"))
        rotation = loc.get("town_rotation", 0.0)
        towns.append({
            "slug": loc["slug"],
            "visibility": loc["visibility"],
            "lat": loc["lat"],
            "lon": loc["lon"],
            "rotation": rotation,
            "features": build_town_overlay(ftg, loc["lat"], loc["lon"], rotation),
        })
    return towns


def player_towns(towns: list[dict]) -> list[dict]:
    """Player copy: the rule `_player_locations_geojson` applies to pins, so a
    `gm_secrets` town is absent."""
    return [t for t in towns if t.get("visibility", "public") != "gm_secrets"]


def feature_collection(towns: list[dict]) -> dict:
    """All towns' features as one GeoJSON FeatureCollection (the map's source data)."""
    return {"type": "FeatureCollection",
            "features": [f for t in towns for f in t["features"]]}


def town_index(towns: list[dict]) -> list[dict]:
    """What the Workshop needs to turn a town on screen without a rebuild: for each town
    its slug, centre, metres per degree there, the rotation it was built with, and where
    its features sit in `feature_collection(towns)` (`start`, `count`). The geometry is
    not sent twice; the page turns the built coordinates by the difference in angle."""
    out, start = [], 0
    for t in towns:
        m_lat, m_lon = metres_per_degree(t["lat"])
        out.append({"slug": t["slug"], "lat": t["lat"], "lon": t["lon"],
                    "mLat": m_lat, "mLon": m_lon, "rotation": t["rotation"],
                    "start": start, "count": len(t["features"])})
        start += len(t["features"])
    return out
