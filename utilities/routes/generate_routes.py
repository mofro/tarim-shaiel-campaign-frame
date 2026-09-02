#!/usr/bin/env python3
"""
Re-route Silk Road segments via OSRM (foot profile).

Reads world/data/tarim-shaiel-routes.geojson, calls the free public OSRM
API for each LineString feature using its current first and last coordinates
as endpoints, and replaces the intermediate vertices with a road-following
path. All segment properties (kind, label, stroke, etc.) are preserved.

Fallback: if OSRM returns no route, errors, or a path longer than 3× the
straight-line haversine distance, the original geometry is kept unchanged.

Results are cached in world/data/.routes_cache.json so subsequent runs do
not re-query the API unless the cache is cleared.

Usage:
    python utilities/routes/generate_routes.py
    python utilities/routes/generate_routes.py --segment route_seg_karmana_rabati-malik
    python utilities/routes/generate_routes.py --dry-run
    python utilities/routes/generate_routes.py --clear-cache
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

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent

ROUTES_PATH    = VAULT_ROOT / "world" / "data" / "tarim-shaiel-routes.geojson"
CACHE_PATH     = VAULT_ROOT / "world" / "data" / ".routes_cache.json"
LOCATIONS_DIR  = VAULT_ROOT / "world" / "locations"

OSRM_BASE   = "http://router.project-osrm.org/route/v1/foot"
FALLBACK_RATIO = 3.0   # keep original if OSRM route > 3× straight-line distance
SNAP_TOLERANCE_KM = 0.5  # max distance OSRM may snap an endpoint before we distrust the result
ENDPOINT_MOVE_THRESHOLD_KM = 0.25  # min real-world distance to treat a location as "moved"
REQUEST_TIMEOUT = 30   # seconds


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


def path_length_km(coords: list[list[float]]) -> float:
    total = 0.0
    for i in range(len(coords) - 1):
        total += haversine_km(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
    return total


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, indent=2), encoding="utf-8")


def _cache_key(lon1: float, lat1: float, lon2: float, lat2: float) -> str:
    return f"{lon1:.4f},{lat1:.4f};{lon2:.4f},{lat2:.4f}"


# ---------------------------------------------------------------------------
# Location endpoint resync
# ---------------------------------------------------------------------------
#
# A route's geometry is a frozen snapshot taken when the route was created
# (or last regenerated) — it does not track later moves to the locations it
# connects (e.g. via the workshop's Edit Coords drag, which only rewrites
# the location's own .md frontmatter). Route IDs encode both endpoint slugs
# as "route_(seg|spur)_{slugA}_{slugB}" (slugs use hyphens, never
# underscores, so splitting the remainder on a single "_" is unambiguous).
# Before routing, we re-read each endpoint location's current coordinates
# and overwrite the feature's first/last vertex with them, so "Regenerate"
# reflects a moved location instead of silently re-snapping stale points.

_ROUTE_ID_RE = re.compile(r"^route_(?:seg|spur)_([^_]+(?:-[^_]+)*)_([^_]+(?:-[^_]+)*)$")


def _parse_route_slugs(route_id: str) -> Optional[tuple[str, str]]:
    m = _ROUTE_ID_RE.match(route_id)
    if not m:
        return None
    return m.group(1), m.group(2)


def _location_lonlat(slug: str) -> Optional[tuple[float, float]]:
    """Read a location's current [lon, lat] from its .md frontmatter, or None."""
    path = LOCATIONS_DIR / f"{slug}.md"
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    fm_match = re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL)
    if not fm_match:
        return None
    fm = fm_match.group(1)

    block = re.search(r"^location:\s*\n((?:[ \t]*-[^\n]*\n)+)", fm, re.MULTILINE)
    if block:
        nums = re.findall(r"-\s*(-?\d+\.?\d*)", block.group(1))
    else:
        inline = re.search(r"^location:\s*\[([^\]]+)\]", fm, re.MULTILINE)
        nums = re.findall(r"-?\d+\.?\d*", inline.group(1)) if inline else []

    if len(nums) != 2:
        return None
    lat, lon = float(nums[0]), float(nums[1])
    return lon, lat


def _resync_endpoints(feat: dict) -> dict:
    """Return feat with its first/last coordinate replaced by the current
    location coordinates for the two slugs in its ID, if both resolve."""
    slugs = _parse_route_slugs(feat.get("id", ""))
    if slugs is None:
        return feat
    start = _location_lonlat(slugs[0])
    end = _location_lonlat(slugs[1])
    if start is None or end is None:
        return feat

    coords = feat["geometry"]["coordinates"]
    old_start, old_end = coords[0], coords[-1]

    # Location .md frontmatter stores 4-decimal coordinates (~11m precision)
    # while route geometry was recorded at 6 decimals, so raw values never
    # match exactly even when nothing moved — compare real distance instead,
    # well above that rounding noise, well below a deliberate drag-to-move.
    moved_start = haversine_km(start[0], start[1], old_start[0], old_start[1]) > ENDPOINT_MOVE_THRESHOLD_KM
    moved_end   = haversine_km(end[0], end[1], old_end[0], old_end[1]) > ENDPOINT_MOVE_THRESHOLD_KM
    if not moved_start and not moved_end:
        return feat

    print("    endpoint moved — resyncing to current location coordinates")
    new_coords = [list(start)] + coords[1:-1] + [list(end)]
    return {**feat, "geometry": {**feat["geometry"], "coordinates": new_coords}}


# ---------------------------------------------------------------------------
# OSRM
# ---------------------------------------------------------------------------

def osrm_route(lon1: float, lat1: float, lon2: float, lat2: float,
               cache: dict, force: bool = False) -> Optional[list[list[float]]]:
    """Return road-following coordinate list from OSRM, or None on failure.

    force=True skips the cache lookup (used by a manual single-route
    "Regenerate" so a previously-failed or already-cached result doesn't
    silently short-circuit a deliberate retry) but still writes the fresh
    result back to cache afterward.
    """
    key = _cache_key(lon1, lat1, lon2, lat2)
    if not force and key in cache:
        return cache[key]

    url = f"{OSRM_BASE}/{lon1},{lat1};{lon2},{lat2}?geometries=geojson&overview=full"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "tarim-shaiel-route-generator/1.0"})
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        print(f"    OSRM network error: {e}", file=sys.stderr)
        cache[key] = None
        return None
    except Exception as e:
        print(f"    OSRM unexpected error: {e}", file=sys.stderr)
        cache[key] = None
        return None

    if data.get("code") != "Ok" or not data.get("routes"):
        cache[key] = None
        return None

    coords = data["routes"][0]["geometry"]["coordinates"]
    cache[key] = coords
    return coords


# ---------------------------------------------------------------------------
# Route a single feature
# ---------------------------------------------------------------------------

def route_feature(feat: dict, cache: dict, dry_run: bool = False, force: bool = False) -> tuple[dict, str]:
    """
    Attempt to replace the feature's geometry with an OSRM-routed path.
    Returns (updated_feature, status) where status is one of:
      "routed"   — OSRM path used
      "fallback" — kept original (OSRM failed or implausible)
      "dry_run"  — would have called OSRM but skipped
    """
    coords = feat["geometry"]["coordinates"]
    if len(coords) < 2:
        return feat, "fallback"

    start = coords[0]
    end   = coords[-1]
    straight_km = haversine_km(start[0], start[1], end[0], end[1])

    if dry_run:
        return feat, "dry_run"

    routed = osrm_route(start[0], start[1], end[0], end[1], cache, force=force)

    if routed is None or len(routed) < 2:
        return feat, "fallback"

    # OSRM silently snaps an unreachable point (e.g. no OSM road/path data
    # nearby, common in remote desert terrain) to whatever it *can* route
    # to, rather than erroring — so a valid-looking response can still end
    # nowhere near the requested location. Distrust it if either endpoint
    # snapped further than SNAP_TOLERANCE_KM and fall back to a straight
    # line to the real (current) endpoints instead of a wrong destination.
    snap_start_km = haversine_km(routed[0][0], routed[0][1], start[0], start[1])
    snap_end_km   = haversine_km(routed[-1][0], routed[-1][1], end[0], end[1])
    if snap_start_km > SNAP_TOLERANCE_KM or snap_end_km > SNAP_TOLERANCE_KM:
        print(
            f"    fallback: OSRM snapped {max(snap_start_km, snap_end_km):.1f}km from "
            f"requested endpoint (no road coverage there) — using straight line",
            file=sys.stderr,
        )
        straight = {**feat, "geometry": {**feat["geometry"], "coordinates": [start, end]}}
        return straight, "fallback"

    routed_km = path_length_km(routed)
    if straight_km > 0 and routed_km > FALLBACK_RATIO * straight_km:
        print(
            f"    fallback: routed={routed_km:.0f}km > {FALLBACK_RATIO}× "
            f"straight={straight_km:.0f}km",
            file=sys.stderr,
        )
        return feat, "fallback"

    updated = {**feat, "geometry": {**feat["geometry"], "coordinates": routed}}
    return updated, "routed"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Re-route Tarim-Shaiel route segments via OSRM foot routing."
    )
    parser.add_argument(
        "--segment",
        help="Process only this segment ID (e.g. route_seg_karmana_rabati-malik)",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would happen without calling OSRM or writing files.",
    )
    parser.add_argument(
        "--clear-cache", action="store_true",
        help="Delete the OSRM cache before running.",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Bypass the cache (including cached failures) and always re-query OSRM.",
    )
    parser.add_argument(
        "--out", default=str(ROUTES_PATH),
        help=f"Output path (default: {ROUTES_PATH.name})",
    )
    args = parser.parse_args()

    if args.clear_cache and CACHE_PATH.exists():
        CACHE_PATH.unlink()
        print("  Cache cleared.")

    if not ROUTES_PATH.exists():
        print(f"ERROR: {ROUTES_PATH} not found", file=sys.stderr)
        return 1

    geojson = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    features = geojson.get("features", [])
    cache = _load_cache()

    out_features = []
    counts = {"routed": 0, "fallback": 0, "dry_run": 0, "skipped": 0}

    for feat in features:
        fid = feat.get("id", "")

        if args.segment and fid != args.segment:
            out_features.append(feat)
            counts["skipped"] += 1
            continue

        coords = feat.get("geometry", {}).get("coordinates", [])
        if len(coords) < 2:
            out_features.append(feat)
            counts["skipped"] += 1
            continue

        feat = _resync_endpoints(feat)
        coords = feat["geometry"]["coordinates"]
        start = coords[0]
        end   = coords[-1]
        straight_km = haversine_km(start[0], start[1], end[0], end[1])

        print(f"  {fid}  ({straight_km:.0f} km straight-line)")

        updated, status = route_feature(feat, cache, dry_run=args.dry_run, force=args.force)
        out_features.append(updated)
        counts[status] += 1

        if status == "routed":
            new_pts = len(updated["geometry"]["coordinates"])
            print(f"    → routed: {new_pts} points")
        elif status == "fallback":
            final_pts = len(updated["geometry"]["coordinates"])
            print(f"    → fallback ({final_pts} points)")
        else:
            print(f"    → {status}")

        # Polite pause between real API calls
        if not args.dry_run and status in ("routed", "fallback"):
            time.sleep(0.5)

    if not args.dry_run:
        _save_cache(cache)

        out_path = Path(args.out)
        out_path.write_text(
            json.dumps({**geojson, "features": out_features}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"\n  Written: {out_path.name}")

    print(
        f"\n  Results: routed={counts['routed']}  fallback={counts['fallback']}  "
        f"dry_run={counts['dry_run']}  skipped={counts['skipped']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
