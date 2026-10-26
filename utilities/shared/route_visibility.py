"""
Which routes players may see.

A route is player-visible only when BOTH hold:
  1. its own `visibility` property is "public", and
  2. the locations at both ends are public.

Endpoints are matched geometrically: the nearest location within MATCH_KM of the
line's first / last coordinate, matched against ALL locations (not just public
ones, or a route ending at a hidden town could "match" a public neighbour).

Fail closed: a missing `visibility`, an unmatched endpoint, or a missing end
location all make the route GM-only. Unmatched endpoints are reported so the GM
can fix the route.
"""

from __future__ import annotations

import sys

from shared.travel_time import _haversine_km

MATCH_KM = 1.0
GM_ONLY = "gm_secrets"
PUBLIC = "public"


def _location_points(locations_gj: dict) -> list:
    """[(lon, lat, visibility, slug)] for every located feature."""
    pts = []
    for f in locations_gj.get("features", []):
        geom = f.get("geometry") or {}
        if geom.get("type") != "Point":
            continue
        lon, lat = geom["coordinates"][:2]
        props = f.get("properties", {})
        pts.append((lon, lat, props.get("visibility", PUBLIC),
                    props.get("slug") or props.get("_slug") or f.get("id", "")))
    return pts


def _nearest(points: list, lon: float, lat: float):
    best, best_km = None, MATCH_KM
    for p in points:
        km = _haversine_km(lon, lat, p[0], p[1])
        if km <= best_km:
            best, best_km = p, km
    return best


def route_endpoints(feature: dict, points: list) -> tuple:
    """(start_loc, end_loc) matched from the line's first and last coordinate.

    Each is a (lon, lat, visibility, slug) tuple or None when nothing is within
    MATCH_KM.
    """
    coords = (feature.get("geometry") or {}).get("coordinates") or []
    if len(coords) < 2:
        return None, None
    return (_nearest(points, coords[0][0], coords[0][1]),
            _nearest(points, coords[-1][0], coords[-1][1]))


def route_is_public(feature: dict, points: list) -> bool:
    if feature.get("properties", {}).get("visibility") != PUBLIC:
        return False
    a, b = route_endpoints(feature, points)
    return bool(a and b and a[2] != GM_ONLY and b[2] != GM_ONLY)


def visible_routes(routes_gj: dict | None, all_locations_gj: dict | None,
                   warn: bool = True) -> dict:
    """Player copy of the routes FeatureCollection.

    `all_locations_gj` must hold EVERY location (hidden ones included) with its
    `visibility` property.
    """
    if not routes_gj:
        return routes_gj or {"type": "FeatureCollection", "features": []}
    points = _location_points(all_locations_gj or {})
    kept = []
    for f in routes_gj.get("features", []):
        if route_is_public(f, points):
            kept.append(f)
        elif warn and f.get("properties", {}).get("visibility") == PUBLIC:
            a, b = route_endpoints(f, points)
            if not (a and b):
                print(f"  WARN: route {f.get('id', '?')} is public but an end matches "
                      f"no location within {MATCH_KM:g} km; kept GM-only", file=sys.stderr)
    return {**routes_gj, "features": kept}


def route_ids(routes_gj: dict | None) -> set:
    return {f.get("id") for f in (routes_gj or {}).get("features", [])}


def visible_waystations(waystations_gj: dict | None, routes_gj: dict | None) -> dict | None:
    """Waystations belonging to the routes still present in `routes_gj`.

    A waystation names its route in `properties.route_segment`; ones with no
    matching visible route are dropped (a waystation with no `route_segment` is
    dropped too, since its route can't be shown public).
    """
    if not waystations_gj:
        return waystations_gj
    ids = route_ids(routes_gj)
    return {**waystations_gj, "features": [
        f for f in waystations_gj.get("features", [])
        if f.get("properties", {}).get("route_segment") in ids
    ]}
