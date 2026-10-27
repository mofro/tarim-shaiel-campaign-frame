"""
Saved travel journeys: the Workshop travel planner's output, kept in
world/data/tarim-shaiel-journeys.geojson.

One journey is one GeoJSON Feature. Its geometry is a MultiLineString with one
line per leg, so leg i of `properties.legs` is `geometry.coordinates[i]`:

    properties.name        display name
    properties.visibility  "public" | "gm_secrets"   (new journeys are gm_secrets)
    properties.stops       [{lng, lat, name, slug?}], one more than there are legs
    properties.legs        [{mode, path, slope_factor?}]
    properties.created / updated   ISO dates

`mode` and `path` are the travel_time vocabulary; a leg's time is never stored, it
is computed from its length, mode and path so a change to the speed table shows up
everywhere.

Players see a journey only under the same fail-closed rule as routes
(route_visibility): its own visibility is public AND no stop sits on a hidden
location. Free points (stops that match no location) are fine.
"""

from __future__ import annotations

import datetime
import json
import os
import re
from pathlib import Path

from shared import travel_time
from shared.route_visibility import GM_ONLY, PUBLIC, _location_points, _nearest

STALE_M = 50.0          # the Workshop recomputes a leg whose stop location moved this far (metres)
MAX_STOPS = 64
MAX_NAME = 120
MAX_STOP_NAME = 80
MAX_LEG_POINTS = 6000
LEG_PATHS = tuple(travel_time.PATH_FACTORS)
VISIBILITIES = (PUBLIC, GM_ONLY)

EMPTY = {"type": "FeatureCollection", "features": []}

_PATH_LABELS = {"road": "road", "terrain": "terrain", "straight": "straight line"}
_COORD_PAIR_RE = re.compile(r"\[\s*(-?\d+(?:\.\d+)?),\s*(-?\d+(?:\.\d+)?)\s*\]")


class JourneyError(ValueError):
    """A journey body the store refuses; the message is shown to the GM."""


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def _num(value, what: str, lo: float, hi: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise JourneyError(f"{what} must be a number")
    if not lo <= value <= hi:
        raise JourneyError(f"{what} out of range")
    return round(float(value), 6)


def _clean_stop(raw, i: int) -> dict:
    if not isinstance(raw, dict):
        raise JourneyError(f"stop {i + 1} must be an object")
    stop = {
        "lng": _num(raw.get("lng"), f"stop {i + 1} lng", -180, 180),
        "lat": _num(raw.get("lat"), f"stop {i + 1} lat", -90, 90),
        "name": str(raw.get("name") or f"Stop {i + 1}").strip()[:MAX_STOP_NAME],
    }
    slug = raw.get("slug")
    if slug:
        if not isinstance(slug, str) or not re.fullmatch(r"[\w.-]+", slug):
            raise JourneyError(f"stop {i + 1} slug is not valid")
        stop["slug"] = slug
    return stop


def _clean_leg(raw, i: int) -> tuple:
    """(leg properties, coordinate line) for leg i."""
    if not isinstance(raw, dict):
        raise JourneyError(f"leg {i + 1} must be an object")
    mode = raw.get("mode")
    if mode not in travel_time.SPEEDS:
        raise JourneyError(f"leg {i + 1} mode must be one of {', '.join(travel_time.SPEEDS)}")
    path = raw.get("path")
    if path not in LEG_PATHS:
        raise JourneyError(f"leg {i + 1} path must be one of {', '.join(LEG_PATHS)}")
    coords = raw.get("coords")
    if not isinstance(coords, list) or len(coords) < 2:
        raise JourneyError(f"leg {i + 1} needs at least two coordinates")
    if len(coords) > MAX_LEG_POINTS:
        raise JourneyError(f"leg {i + 1} has more than {MAX_LEG_POINTS} points")
    line = []
    for pt in coords:
        if not isinstance(pt, (list, tuple)) or len(pt) < 2:
            raise JourneyError(f"leg {i + 1} has a malformed coordinate")
        line.append([_num(pt[0], f"leg {i + 1} lng", -180, 180),
                     _num(pt[1], f"leg {i + 1} lat", -90, 90)])
    leg = {"mode": mode, "path": path}
    if raw.get("slope_factor") is not None:
        leg["slope_factor"] = _num(raw["slope_factor"], f"leg {i + 1} slope_factor", 0.05, 2)
    return leg, line


def clean_journey(data) -> dict:
    """Validated {name, stops, legs, lines[, visibility]} from a request body.

    Raises JourneyError. Derived fields (geometry, ids, dates) are never taken
    from the body.
    """
    if not isinstance(data, dict):
        raise JourneyError("body must be an object")
    name = str(data.get("name") or "").strip()
    if not name:
        raise JourneyError("name is required")
    stops_raw, legs_raw = data.get("stops"), data.get("legs")
    if not isinstance(stops_raw, list) or not isinstance(legs_raw, list):
        raise JourneyError("stops and legs must be lists")
    if not 2 <= len(stops_raw) <= MAX_STOPS:
        raise JourneyError(f"a journey needs 2 to {MAX_STOPS} stops")
    if len(legs_raw) != len(stops_raw) - 1:
        raise JourneyError("a journey needs exactly one leg between each pair of stops")
    legs, lines = [], []
    for i, raw in enumerate(legs_raw):
        leg, line = _clean_leg(raw, i)
        legs.append(leg)
        lines.append(line)
    out = {
        "name": name[:MAX_NAME],
        "stops": [_clean_stop(s, i) for i, s in enumerate(stops_raw)],
        "legs": legs,
        "lines": lines,
    }
    if "visibility" in data:
        out["visibility"] = check_visibility(data["visibility"])
    return out


def check_visibility(value) -> str:
    if value not in VISIBILITIES:
        raise JourneyError(f"visibility must be one of {', '.join(VISIBILITIES)}")
    return value


# ---------------------------------------------------------------------------
# Store
# ---------------------------------------------------------------------------

def _today() -> str:
    return datetime.date.today().isoformat()


def slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:60] or "journey"


def new_id(name: str, taken) -> str:
    """`journey_<slug of name>`, with -2, -3 ... on a collision."""
    base = f"journey_{slugify(name)}"
    taken = set(taken)
    jid, n = base, 1
    while jid in taken:
        n += 1
        jid = f"{base}-{n}"
    return jid


def build_feature(jid: str, clean: dict, visibility: str, created: str, updated: str) -> dict:
    return {
        "type": "Feature",
        "id": jid,
        "properties": {
            "name": clean["name"],
            "visibility": visibility,
            "created": created,
            "updated": updated,
            "stops": clean["stops"],
            "legs": clean["legs"],
        },
        "geometry": {"type": "MultiLineString", "coordinates": clean["lines"]},
    }


def serialize(gj: dict) -> str:
    """Pretty JSON with one coordinate pair per line, so a diff shows real changes."""
    text = json.dumps(gj, indent=2, ensure_ascii=False)
    return _COORD_PAIR_RE.sub(r"[\1, \2]", text) + "\n"


def load(path: Path) -> dict:
    if not path.exists():
        return {"type": "FeatureCollection", "features": []}
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, gj: dict) -> None:
    """Atomic write: a crash mid-write cannot leave a half-written journeys file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_text(serialize(gj), encoding="utf-8")
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


def config_json() -> str:
    """Limits the Workshop JS shares with the store, as JSON for `var _JRN = ...`."""
    return json.dumps({"staleM": STALE_M, "maxStops": MAX_STOPS, "maxName": MAX_NAME},
                      separators=(",", ":"))


def find(gj: dict, jid: str):
    return next((f for f in gj.get("features", []) if f.get("id") == jid), None)


def create(path: Path, data) -> dict:
    """Save a new journey (gm_secrets unless the body says otherwise)."""
    clean = clean_journey(data)
    gj = load(path)
    jid = new_id(clean["name"], (f.get("id") for f in gj["features"]))
    feat = build_feature(jid, clean, clean.get("visibility", GM_ONLY), _today(), _today())
    gj["features"].append(feat)
    save(path, gj)
    return feat


def replace(path: Path, jid: str, data):
    """Overwrite a journey's name, stops and legs; its id, visibility and created
    date stay. None when the id does not exist."""
    clean = clean_journey(data)
    gj = load(path)
    old = find(gj, jid)
    if old is None:
        return None
    props = old["properties"]
    visibility = clean.get("visibility", props.get("visibility", GM_ONLY))
    feat = build_feature(jid, clean, visibility, props.get("created", _today()), _today())
    gj["features"] = [feat if f.get("id") == jid else f for f in gj["features"]]
    save(path, gj)
    return feat


def patch(path: Path, jid: str, data):
    """Change a journey's name and/or visibility only. None when not found."""
    if not isinstance(data, dict):
        raise JourneyError("body must be an object")
    fields = {}
    if "name" in data:
        name = str(data["name"] or "").strip()
        if not name:
            raise JourneyError("name is required")
        fields["name"] = name[:MAX_NAME]
    if "visibility" in data:
        fields["visibility"] = check_visibility(data["visibility"])
    if not fields:
        raise JourneyError("no recognised fields")
    gj = load(path)
    feat = find(gj, jid)
    if feat is None:
        return None
    feat["properties"].update(fields)
    feat["properties"]["updated"] = _today()
    save(path, gj)
    return feat


def delete(path: Path, jid: str) -> bool:
    gj = load(path)
    kept = [f for f in gj.get("features", []) if f.get("id") != jid]
    if len(kept) == len(gj.get("features", [])):
        return False
    gj["features"] = kept
    save(path, gj)
    return True


# ---------------------------------------------------------------------------
# Times
# ---------------------------------------------------------------------------

def leg_km(feature: dict, i: int) -> float:
    return travel_time.line_length_km(feature["geometry"]["coordinates"][i])


def leg_hours(feature: dict, i: int) -> float:
    leg = feature["properties"]["legs"][i]
    return travel_time.segment_hours(
        leg_km(feature, i), leg.get("mode"), leg.get("path"), leg.get("slope_factor", 1.0))


def summary(feature: dict) -> dict:
    """{name, legs: [{from, to, mode, path, km, hours}], total_km, total_hours}."""
    props = feature["properties"]
    stops, legs = props.get("stops", []), props.get("legs", [])
    rows = []
    for i, leg in enumerate(legs):
        rows.append({
            "from": stops[i]["name"], "to": stops[i + 1]["name"],
            "mode": travel_time.normalize_mode(leg.get("mode")), "path": leg.get("path"),
            "km": leg_km(feature, i), "hours": leg_hours(feature, i),
        })
    return {
        "name": props.get("name", ""), "legs": rows,
        "total_km": sum(r["km"] for r in rows), "total_hours": sum(r["hours"] for r in rows),
    }


def _fmt_km(km: float) -> str:
    return f"{km:.0f} km" if km >= 10 else f"{km:.1f} km"


def popup_info(feature: dict) -> dict:
    """Pre-formatted popup content (strings only), the one shape the maps render."""
    s = summary(feature)
    rows = []
    for r in s["legs"]:
        spec = travel_time.SPEEDS[r["mode"]]
        how = spec["label"] if spec["fly"] else f'{spec["label"]}, {_PATH_LABELS.get(r["path"], "")}'
        rows.append({
            "from": r["from"], "to": r["to"], "how": how,
            "km": _fmt_km(r["km"]), "time": travel_time.format_duration(r["hours"], approx=True),
        })
    return {
        "name": s["name"], "legs": rows,
        "total": f'{_fmt_km(s["total_km"])} · {travel_time.format_duration(s["total_hours"], approx=True)}',
    }


# ---------------------------------------------------------------------------
# Visibility
# ---------------------------------------------------------------------------

def _slug_of(point) -> str:
    slug = point[3]
    return slug[len("location_"):] if slug.startswith("location_") else slug


def journey_is_public(feature: dict, points: list) -> bool:
    """Own visibility public AND no stop on a hidden location (fails closed)."""
    props = feature.get("properties", {})
    if props.get("visibility") != PUBLIC:
        return False
    stops = props.get("stops") or []
    if len(stops) < 2:
        return False
    by_slug = {_slug_of(p): p for p in points}
    for stop in stops:
        slug = stop.get("slug")
        if slug:
            loc = by_slug.get(slug)
            if loc is None or loc[2] == GM_ONLY:
                return False
        near = _nearest(points, stop["lng"], stop["lat"])
        if near is not None and near[2] == GM_ONLY:
            return False
    return True


def visible_journeys(journeys_gj: dict | None, all_locations_gj: dict | None) -> dict:
    """Player copy of the journeys. `all_locations_gj` must hold EVERY location,
    hidden ones included, with its `visibility` property."""
    if not journeys_gj:
        return {"type": "FeatureCollection", "features": []}
    points = _location_points(all_locations_gj or {})
    kept = [f for f in journeys_gj.get("features", []) if journey_is_public(f, points)]
    return {**journeys_gj, "features": kept}


def annotate_player_visible(journeys_gj: dict | None, all_locations_gj: dict | None) -> dict:
    """Workshop copy with `_playerVisible` per journey (to dim the hidden ones)."""
    if not journeys_gj:
        return {"type": "FeatureCollection", "features": []}
    points = _location_points(all_locations_gj or {})
    feats = [{**f, "properties": {**f.get("properties", {}), "id": f.get("id"),
                                  "_playerVisible": journey_is_public(f, points)}}
             for f in journeys_gj.get("features", [])]
    return {**journeys_gj, "features": feats}


def _payload(features: list) -> tuple:
    """(FeatureCollection, {id: popup_info}) for the given journey features.

    Features carry only an id and the name; stop coordinates, slugs, dates and
    the visibility flag stay out of the page source.
    """
    feats, info = [], {}
    for f in features:
        jid = f["id"]
        feats.append({"type": "Feature", "id": jid,
                      "properties": {"id": jid, "name": f["properties"].get("name", "")},
                      "geometry": f["geometry"]})
        info[jid] = popup_info(f)
    return {"type": "FeatureCollection", "features": feats}, info


def player_payload(journeys_gj: dict | None, all_locations_gj: dict | None) -> tuple:
    """Player-page payload: only the journeys the players may see."""
    return _payload(visible_journeys(journeys_gj, all_locations_gj)["features"])


def gm_payload(journeys_gj: dict | None) -> tuple:
    """GM-build payload: every journey, hidden ones included."""
    return _payload((journeys_gj or {}).get("features", []))
