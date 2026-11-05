"""
Place Fantasy Town Generator (FTG) town maps on the world map.

An FTG GeoJSON export is in local metres (no CRS, origin at the town centre, +x east,
+y north). The file stays untouched in world/maps/cities/; at Workshop build time each
town is moved to the `location:` of the page whose slug equals the file stem, and
trimmed to what the map draws. The people file (`<Town>.json`) never rides in this
geometry.

Usage (from the Workshop builder):
    towns  = build_overlays(load_all_locations(LOCATIONS_DIR))
    gm     = feature_collection(towns)
    player = feature_collection(player_towns(towns))
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
    """Local metres to [lon, lat], anchored at the town centre."""

    def __init__(self, lat: float, lon: float):
        self.lat = lat
        self.lon = lon
        self.m_lat, self.m_lon = metres_per_degree(lat)

    def to_lonlat(self, x: float, y: float) -> list[float]:
        return [round(self.lon + x / self.m_lon, COORD_DECIMALS),
                round(self.lat + y / self.m_lat, COORD_DECIMALS)]

    def to_local(self, lon: float, lat: float) -> tuple[float, float]:
        return ((lon - self.lon) * self.m_lon, (lat - self.lat) * self.m_lat)

    def ring(self, coords: list) -> list:
        return [self.to_lonlat(x, y) for x, y in coords]


def _geometry(geom: dict, ref: Georeference) -> dict:
    if geom["type"] == "Polygon":
        return {"type": "Polygon", "coordinates": [ref.ring(r) for r in geom["coordinates"]]}
    if geom["type"] == "LineString":
        return {"type": "LineString", "coordinates": ref.ring(geom["coordinates"])}
    raise ValueError(f"unsupported FTG geometry: {geom['type']}")


def build_town_overlay(ftg: dict, lat: float, lon: float) -> list[dict]:
    """Features of one FTG town, georeferenced and trimmed.

    BACKGROUND polygons (lawn / grass / road texture) are not drawn. INVISIBLE edges
    are dropped.
    """
    ref = Georeference(lat, lon)
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
    `{"slug", "visibility", "features"}` entries. Slug and visibility sit on the town,
    not on each feature, which would add about 120 KB for Dehdadi.

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
        towns.append({
            "slug": loc["slug"],
            "visibility": loc["visibility"],
            "features": build_town_overlay(ftg, loc["lat"], loc["lon"]),
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
