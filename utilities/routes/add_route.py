#!/usr/bin/env python3
"""Add one or more route segments to tarim-shaiel-routes.geojson.

Usage:
    # Two waypoints — one segment
    python utilities/routes/add_route.py karmana rabati-malik

    # N waypoints — N-1 consecutive segments
    python utilities/routes/add_route.py balkh dehdadi aybak baghlan charikar kabul

    # Spur (off main route)
    python utilities/routes/add_route.py kashgar stone-ledger-gate --spur

Each pair of adjacent slugs becomes one LineString feature with a straight-line
geometry (two coords). Run generate_routes.py afterwards to snap to roads via OSRM.
"""

import argparse
import json
import math
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent

ROUTES_PATH   = VAULT_ROOT / "world" / "data" / "tarim-shaiel-routes.geojson"
LOCATIONS_PATH = VAULT_ROOT / "world" / "data" / "tarim-shaiel-locations.geojson"

# Default stroke colour for new segments (matches existing route styling)
DEFAULT_STROKE = "#1a1208"
DEFAULT_STROKE_WIDTH = 5
DEFAULT_STROKE_OPACITY = 0.9


def _load_locations() -> dict[str, dict]:
    """Return {slug: {coords, label}} from the locations GeoJSON."""
    if not LOCATIONS_PATH.exists():
        print(f"ERROR: {LOCATIONS_PATH} not found. Run generate_geojson first.", file=sys.stderr)
        sys.exit(1)
    data = json.loads(LOCATIONS_PATH.read_text(encoding="utf-8"))
    result: dict[str, dict] = {}
    for feat in data.get("features", []):
        slug = feat["properties"].get("slug", "")
        if slug:
            result[slug] = {
                "coords": feat["geometry"]["coordinates"],  # [lon, lat]
                "label": feat["properties"].get("label") or feat["properties"].get("title") or slug,
            }
    return result


def _load_routes() -> dict:
    if not ROUTES_PATH.exists():
        print(f"ERROR: {ROUTES_PATH} not found.", file=sys.stderr)
        sys.exit(1)
    return json.loads(ROUTES_PATH.read_text(encoding="utf-8"))


def _existing_ids(geojson: dict) -> set[str]:
    return {f["id"] for f in geojson.get("features", [])}


def _segment_id(slug_a: str, slug_b: str, spur: bool) -> str:
    prefix = "route_spur" if spur else "route_seg"
    return f"{prefix}_{slug_a}_{slug_b}"


def _make_feature(seg_id: str, slug_a: str, slug_b: str,
                  loc_a: dict, loc_b: dict, spur: bool,
                  route_name: str = "", description: str = "",
                  route_type: str = "") -> dict:
    label = f"{loc_a['label']} → {loc_b['label']}"
    props = {
        "kind": "spur" if spur else "route",
        "label": label,
        "title": label,
        "description": description,
        "stroke": DEFAULT_STROKE,
        "stroke-width": DEFAULT_STROKE_WIDTH,
        "stroke-opacity": DEFAULT_STROKE_OPACITY,
    }
    if route_name:
        props["route_name"] = route_name
    if route_type:
        props["route_type"] = route_type
    return {
        "type": "Feature",
        "id": seg_id,
        "properties": props,
        "geometry": {
            "type": "LineString",
            "coordinates": [loc_a["coords"], loc_b["coords"]],
        },
    }


def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add route segment(s) to tarim-shaiel-routes.geojson."
    )
    parser.add_argument("slugs", nargs="+", metavar="SLUG",
                        help="Location slugs in order (2 = one segment, N = N-1 segments)")
    parser.add_argument("--spur", action="store_true",
                        help="Mark as a spur route (route_spur_… id prefix)")
    parser.add_argument("--name", default="",
                        help="Custom route name, shown in place of the auto A → B label")
    parser.add_argument("--description", default="",
                        help="Route description")
    parser.add_argument("--route-type", default="",
                        help="Route type, e.g. trade-route, pilgrimage, military")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be added without writing")
    args = parser.parse_args()

    if len(args.slugs) < 2:
        print("ERROR: at least 2 slugs required.", file=sys.stderr)
        sys.exit(1)

    locs = _load_locations()

    # Validate all slugs exist
    missing = [s for s in args.slugs if s not in locs]
    if missing:
        for s in missing:
            print(f"ERROR: slug '{s}' not found in locations GeoJSON. "
                  f"Add it first with add_location.py then rebuild the GeoJSON.", file=sys.stderr)
        sys.exit(1)

    geojson = _load_routes()
    existing = _existing_ids(geojson)

    # Build segments
    pairs = list(zip(args.slugs, args.slugs[1:]))
    new_features: list[dict] = []
    skipped: list[str] = []

    for slug_a, slug_b in pairs:
        seg_id = _segment_id(slug_a, slug_b, args.spur)
        if seg_id in existing:
            skipped.append(seg_id)
            continue
        feat = _make_feature(seg_id, slug_a, slug_b, locs[slug_a], locs[slug_b], args.spur,
                             route_name=args.name, description=args.description,
                             route_type=args.route_type)
        new_features.append(feat)

    # Report
    if skipped:
        for s in skipped:
            print(f"  SKIP (already exists): {s}")

    if not new_features:
        print("Nothing to add — all segments already exist.")
        return

    for feat in new_features:
        coords = feat["geometry"]["coordinates"]
        km = haversine_km(coords[0][0], coords[0][1], coords[1][0], coords[1][1])
        days = math.ceil(km / 30)
        print(f"  {'[DRY RUN] ' if args.dry_run else ''}Add: {feat['id']}")
        print(f"    {feat['properties']['label']}")
        print(f"    straight-line: ~{km:.0f} km / ~{days} days (30 km/day)")

    if args.dry_run:
        print("\nDry run — nothing written.")
        return

    geojson["features"].extend(new_features)
    ROUTES_PATH.write_text(json.dumps(geojson, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWritten: {ROUTES_PATH.relative_to(VAULT_ROOT)}")
    print(f"  {len(new_features)} segment(s) added (straight-line geometry)")
    print()
    print("Next steps:")
    print("  python utilities/routes/generate_routes.py   # snap to roads via OSRM")
    print("  python utilities/world/generate_map_workshop.py   # refresh workshop map")


if __name__ == "__main__":
    main()
