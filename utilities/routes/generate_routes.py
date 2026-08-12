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
import sys
import time
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent

ROUTES_PATH = VAULT_ROOT / "world" / "data" / "tarim-shaiel-routes.geojson"
CACHE_PATH  = VAULT_ROOT / "world" / "data" / ".routes_cache.json"

OSRM_BASE   = "http://router.project-osrm.org/route/v1/foot"
FALLBACK_RATIO = 3.0   # keep original if OSRM route > 3× straight-line distance
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
# OSRM
# ---------------------------------------------------------------------------

def osrm_route(lon1: float, lat1: float, lon2: float, lat2: float,
               cache: dict) -> Optional[list[list[float]]]:
    """Return road-following coordinate list from OSRM, or None on failure."""
    key = _cache_key(lon1, lat1, lon2, lat2)
    if key in cache:
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

def route_feature(feat: dict, cache: dict, dry_run: bool = False) -> tuple[dict, str]:
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

    routed = osrm_route(start[0], start[1], end[0], end[1], cache)

    if routed is None or len(routed) < 2:
        return feat, "fallback"

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

        start = coords[0]
        end   = coords[-1]
        straight_km = haversine_km(start[0], start[1], end[0], end[1])

        print(f"  {fid}  ({straight_km:.0f} km straight-line)")

        updated, status = route_feature(feat, cache, dry_run=args.dry_run)
        out_features.append(updated)
        counts[status] += 1

        if status == "routed":
            new_pts = len(updated["geometry"]["coordinates"])
            print(f"    → routed: {new_pts} points")
        elif status == "fallback":
            print(f"    → kept original ({len(coords)} points)")
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
