#!/usr/bin/env python3
"""
Place waystation candidates along routed Silk Road segments.

Reads world/data/tarim-shaiel-routes.geojson, walks each LineString at
INTERVAL_KM intervals (default 30 km), and queries the Overpass API for
historically attested settlements or caravanserais within RADIUS_KM (15 km).

Output is world/data/tarim-shaiel-waystations.geojson — committed to git,
reviewed by the author, and rendered as a dim togglable MapLibre layer.

Incremental rebuild: on re-run, features already marked
  approval_status != "candidate"  (i.e. "promoted" / "rejected")
are preserved unchanged. Only the "candidate" pool is regenerated.

Overpass responses are cached in world/data/.waystations_cache.json.

Usage:
    python utilities/routes/place_waystations.py
    python utilities/routes/place_waystations.py --segment route_seg_kashgar_aksu
    python utilities/routes/place_waystations.py --interval 25
    python utilities/routes/place_waystations.py --dry-run
    python utilities/routes/place_waystations.py --clear-cache
"""

import argparse
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error
import urllib.parse

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent

ROUTES_PATH      = VAULT_ROOT / "world" / "data" / "tarim-shaiel-routes.geojson"
WAYSTATIONS_PATH = VAULT_ROOT / "world" / "data" / "tarim-shaiel-waystations.geojson"
CACHE_PATH       = VAULT_ROOT / "world" / "data" / ".waystations_cache.json"

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
REQUEST_TIMEOUT = 30
SLEEP_BETWEEN_QUERIES = 1.2  # seconds — polite rate-limiting


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------

def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def interpolate(p1: list[float], p2: list[float], t: float) -> list[float]:
    """Linear interpolation between two [lon, lat] points, t in [0, 1]."""
    return [p1[0] + t * (p2[0] - p1[0]), p1[1] + t * (p2[1] - p1[1])]


def sample_points_along_path(
    coords: list[list[float]], interval_km: float
) -> list[tuple[float, float, float]]:
    """
    Walk the LineString and return (lon, lat, dist_from_start) for each
    candidate point spaced approximately interval_km apart.
    Skips the exact start and end (those are already known city nodes).
    """
    if len(coords) < 2:
        return []

    points = []
    cumulative = 0.0
    next_target = interval_km

    for i in range(len(coords) - 1):
        seg_len = haversine_km(
            coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1]
        )
        while next_target <= cumulative + seg_len:
            t = (next_target - cumulative) / seg_len if seg_len > 0 else 0
            pt = interpolate(coords[i], coords[i + 1], t)
            points.append((pt[0], pt[1], next_target))
            next_target += interval_km
        cumulative += seg_len

    return points


# ---------------------------------------------------------------------------
# Overpass query
# ---------------------------------------------------------------------------

OVERPASS_QUERY_TEMPLATE = """
[out:json][timeout:25];
(
  node["historic"="caravanserai"](around:{radius},{lat},{lon});
  node["place"~"^(town|village|hamlet)$"](around:{radius},{lat},{lon});
  way["historic"="caravanserai"](around:{radius},{lat},{lon});
  node["amenity"="place_of_worship"]["historic"](around:{radius},{lat},{lon});
);
out center;
""".strip()


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _cache_key(lon: float, lat: float, radius_km: float) -> str:
    return f"{lon:.4f},{lat:.4f},{radius_km:.0f}km"


def overpass_query(
    lon: float, lat: float, radius_km: float, cache: dict
) -> Optional[list[dict]]:
    """Return list of OSM elements near (lon, lat), or None on failure."""
    key = _cache_key(lon, lat, radius_km)
    if key in cache:
        return cache[key]

    query = OVERPASS_QUERY_TEMPLATE.format(
        radius=int(radius_km * 1000), lat=f"{lat:.6f}", lon=f"{lon:.6f}"
    )
    try:
        # Overpass expects form-encoded body: data=<query>
        encoded = urllib.parse.urlencode({"data": query}).encode("utf-8")
        req = urllib.request.Request(
            OVERPASS_URL,
            data=encoded,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "tarim-shaiel-waystation-generator/1.0",
            },
        )
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"    Overpass network error: {e}", file=sys.stderr)
        cache[key] = []
        return []
    except Exception as e:
        print(f"    Overpass unexpected error: {e}", file=sys.stderr)
        cache[key] = []
        return []

    elements = result.get("elements", [])
    cache[key] = elements
    return elements


def _best_element(elements: list[dict]) -> Optional[dict]:
    """Pick the most historically relevant element from an Overpass result set."""
    # Priority: caravanserai > place_of_worship+historic > town > village > hamlet
    def priority(el: dict) -> int:
        tags = el.get("tags", {})
        if tags.get("historic") == "caravanserai":
            return 0
        if tags.get("amenity") == "place_of_worship" and "historic" in tags:
            return 1
        place = tags.get("place", "")
        if place == "town":
            return 2
        if place == "village":
            return 3
        if place == "hamlet":
            return 4
        return 5

    if not elements:
        return None
    return min(elements, key=priority)


def _slug_from(name: str) -> str:
    """Turn a name string into a URL-safe slug."""
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return s[:60]


# ---------------------------------------------------------------------------
# Build waystation feature
# ---------------------------------------------------------------------------

def make_waystation_feature(
    lon: float,
    lat: float,
    dist_km: float,
    route_segment_id: str,
    elements: list[dict],
    candidate_index: int,
) -> dict:
    best = _best_element(elements) if elements else None

    if best:
        tags = best.get("tags", {})
        osm_name = tags.get("name") or tags.get("name:en") or tags.get("int_name")
        # For ways, Overpass returns a 'center' node
        if best["type"] == "way" and "center" in best:
            lon = best["center"]["lon"]
            lat = best["center"]["lat"]
        else:
            lon = best.get("lon", lon)
            lat = best.get("lat", lat)
        osm_id  = str(best.get("id", ""))
        source  = "historic_osm"
        slug    = _slug_from(osm_name) if osm_name else f"waystation-{candidate_index}"
        osm_tags = {k: v for k, v in tags.items() if k in (
            "historic", "place", "amenity", "name", "name:en"
        )}
    else:
        osm_name = None
        osm_id   = None
        source   = "generated"
        slug     = f"waystation-{candidate_index}"
        osm_tags = {}

    return {
        "type": "Feature",
        "properties": {
            "kind":                "waystation",
            "source":              source,
            "osm_id":              osm_id,
            "osm_name":            osm_name,
            "osm_tags":            osm_tags,
            "suggested_slug":      slug,
            "route_segment":       route_segment_id,
            "dist_from_start_km":  round(dist_km, 1),
            "approval_status":     "candidate",
        },
        "geometry": {
            "type": "Point",
            "coordinates": [round(lon, 6), round(lat, 6)],
        },
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Place waystation candidates along routed Silk Road segments."
    )
    parser.add_argument(
        "--segment",
        help="Process only this segment ID.",
    )
    parser.add_argument(
        "--interval", type=float, default=30.0,
        help="Distance between candidates in km (default: 30).",
    )
    parser.add_argument(
        "--radius", type=float, default=15.0,
        help="Overpass search radius in km (default: 15).",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print candidate positions without calling Overpass.",
    )
    parser.add_argument(
        "--clear-cache", action="store_true",
        help="Delete the Overpass cache before running.",
    )
    parser.add_argument(
        "--out", default=str(WAYSTATIONS_PATH),
        help=f"Output path (default: {WAYSTATIONS_PATH.name})",
    )
    args = parser.parse_args()

    if args.clear_cache and CACHE_PATH.exists():
        CACHE_PATH.unlink()
        print("  Cache cleared.")

    if not ROUTES_PATH.exists():
        print(f"ERROR: {ROUTES_PATH} not found", file=sys.stderr)
        return 1

    routes_gj = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    cache = _load_cache()

    # Load existing waystations to preserve promoted/rejected entries
    out_path = Path(args.out)
    preserved: list[dict] = []
    if out_path.exists():
        try:
            existing = json.loads(out_path.read_text(encoding="utf-8"))
            for feat in existing.get("features", []):
                status = feat.get("properties", {}).get("approval_status", "candidate")
                if status != "candidate":
                    preserved.append(feat)
        except Exception:
            pass
    if preserved:
        print(f"  Preserved {len(preserved)} non-candidate feature(s).")

    new_candidates: list[dict] = []
    candidate_index = 0
    total_historic = 0
    total_generated = 0

    for feat in routes_gj.get("features", []):
        fid = feat.get("id", "")

        if args.segment and fid != args.segment:
            continue

        coords = feat.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            continue

        sample_pts = sample_points_along_path(coords, args.interval)
        if not sample_pts:
            continue

        print(f"  {fid}: {len(sample_pts)} candidate(s)")

        for lon, lat, dist_km in sample_pts:
            candidate_index += 1

            if args.dry_run:
                print(f"    [{candidate_index}] {lat:.4f},{lon:.4f} @ {dist_km:.0f}km — (dry run)")
                new_candidates.append(make_waystation_feature(
                    lon, lat, dist_km, fid, [], candidate_index
                ))
                continue

            elements = overpass_query(lon, lat, args.radius, cache) or []
            feat_out = make_waystation_feature(lon, lat, dist_km, fid, elements, candidate_index)
            source = feat_out["properties"]["source"]
            osm_name = feat_out["properties"].get("osm_name") or "(unnamed)"

            if source == "historic_osm":
                total_historic += 1
                print(f"    [{candidate_index}] {dist_km:.0f}km — OSM hit: {osm_name}")
            else:
                total_generated += 1
                print(f"    [{candidate_index}] {dist_km:.0f}km — generated")

            new_candidates.append(feat_out)
            time.sleep(SLEEP_BETWEEN_QUERIES)

    if not args.dry_run:
        _save_cache(cache)

    all_features = preserved + new_candidates
    output_gj = {"type": "FeatureCollection", "features": all_features}

    if not args.dry_run:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(output_gj, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n  Written: {out_path.name}")

    print(
        f"\n  Results: {len(new_candidates)} new candidates "
        f"({total_historic} historic OSM, {total_generated} generated)"
    )
    if preserved:
        print(f"           {len(preserved)} existing non-candidate feature(s) preserved")

    return 0


if __name__ == "__main__":
    sys.exit(main())
