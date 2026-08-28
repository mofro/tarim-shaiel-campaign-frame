#!/usr/bin/env python3
"""Add a new location stub to world/locations/.

Usage:
    python utilities/world/add_location.py \
        --name "Nur-Ata" --lat 40.5628 --lon 65.6904 \
        --category route-node --region central-asian-hubs

All arguments can also be supplied interactively (run with no flags).
"""

import argparse
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent
LOCATIONS_DIR = VAULT_ROOT / "world" / "locations"

VALID_CATEGORIES = {
    "caravanserai",
    "capital",
    "city",
    "town",
    "fortress",
    "sacred-site",
    "ruins",
    "route-node",
    "water-body",
    "landmark",
    "mythic-landscape",
}

VALID_VISIBILITY = {"public", "gm_secrets"}


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = normalized.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug


def build_frontmatter(
    name: str,
    slug: str,
    lat: float,
    lon: float,
    category: str,
    fantasy_name: str,
    description: str,
    region: str,
    visibility: str,
    today: str,
) -> str:
    lines = [
        "---",
        f"title: {name}",
        "project: TTRPG_Tarim_Shaiel",
    ]
    if region:
        lines.append(f"parent_region: {region}")
    lines += [
        "domain: world",
        "doc_type: canon",
        "content_type: location",
        f"visibility: {visibility}",
        "status: draft",
        f"created: {today}",
        f'description: "{description}"',
    ]
    if fantasy_name:
        lines.append(f"fantasy_name: {fantasy_name}")
    lines += [
        f"last_updated: {today}",
        "location:",
        f"- {lat}",
        f"- {lon}",
        "map_min_zoom: 5",
        "map_max_zoom: 14",
        f"mapmarker: {category}",
        f"name: {name}",
        f"real_world_name: {name}",
        "tags:",
        "- placeholder",
        f"- type-{category}",
        f"type: {category}",
        "---",
    ]
    return "\n".join(lines)


def build_leaflet_block(slug: str) -> str:
    return (
        f"```leaflet\n"
        f"id: location-{slug}\n"
        f"coordinates: [[world/locations/{slug}]]\n"
        f"defaultZoom: 10\n"
        f"minZoom: 4.5\n"
        f"maxZoom: 18\n"
        f"height: 500px\n"
        f"osmLayer: false\n"
        f"tileServer:\n"
        f"  - https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{{z}}/{{y}}/{{x}}|Satellite\n"
        f"\n"
        f"geojson:\n"
        f"  - [[world/tarim-shaiel-routes.geojson]]|Routes\n"
        f"  - [[world/tarim-shaiel-locations.geojson]]|Locations\n"
        f"```"
    )


def build_stub(
    name: str,
    slug: str,
    lat: float,
    lon: float,
    category: str,
    fantasy_name: str,
    description: str,
    region: str,
    visibility: str,
    today: str,
) -> str:
    fm = build_frontmatter(
        name, slug, lat, lon, category, fantasy_name,
        description, region, visibility, today,
    )
    leaflet = build_leaflet_block(slug)
    display = fantasy_name if fantasy_name else name
    body = f"""
{leaflet}

# {display}

> **PLACEHOLDER.** Coordinates, marker, and region are locked; prose has not been written. Do not treat any narrative detail below as canon — there isn't any yet.

## Key Features

## Factions Present

## Resources

## Notable Nearby Locations
"""
    return fm + "\n\n" + body.lstrip()


def prompt(label: str, required: bool = False, default: str = "") -> str:
    suffix = " (required)" if required else (f" [{default}]" if default else " [optional]")
    while True:
        val = input(f"{label}{suffix}: ").strip()
        if not val and default:
            return default
        if not val and required:
            print(f"  {label} is required.")
            continue
        return val


def interactive_mode() -> argparse.Namespace:
    print("add_location — interactive mode\n")
    name = prompt("Name", required=True)
    lat_s = prompt("Latitude", required=True)
    lon_s = prompt("Longitude", required=True)
    print(f"  Categories: {', '.join(sorted(VALID_CATEGORIES))}")
    category = prompt("Category", required=True)
    fantasy_name = prompt("Fantasy name")
    region = prompt("Region")
    print(f"  Visibility options: {', '.join(sorted(VALID_VISIBILITY))}")
    visibility = prompt("Visibility", default="public")
    description = prompt("Description", default="PLACEHOLDER — location pending. Prose pass pending.")
    dry_run = prompt("Dry run? [y/N]", default="n").lower().startswith("y")

    ns = argparse.Namespace(
        name=name,
        lat=float(lat_s),
        lon=float(lon_s),
        category=category,
        fantasy_name=fantasy_name,
        region=region,
        visibility=visibility,
        description=description,
        dry_run=dry_run,
    )
    return ns


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add a new location stub to world/locations/."
    )
    parser.add_argument("--name", help="Display name of the location")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")
    parser.add_argument("--category", help=f"Marker category: {', '.join(sorted(VALID_CATEGORIES))}")
    parser.add_argument("--fantasy-name", default="", help="In-world name (optional)")
    parser.add_argument("--description", default="PLACEHOLDER — location pending. Prose pass pending.",
                        help="Short description for frontmatter")
    parser.add_argument("--region", default="", help="parent_region slug (optional)")
    parser.add_argument("--visibility", default="public",
                        choices=list(VALID_VISIBILITY), help="public or gm_secrets")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the file content without writing")

    args = parser.parse_args()

    # If no required args given, drop into interactive mode
    if args.name is None and args.lat is None and args.lon is None:
        args = interactive_mode()

    # Validate required fields
    errors = []
    if not args.name:
        errors.append("--name is required")
    if args.lat is None:
        errors.append("--lat is required")
    if args.lon is None:
        errors.append("--lon is required")
    if not args.category:
        errors.append("--category is required")
    elif args.category not in VALID_CATEGORIES:
        errors.append(f"--category must be one of: {', '.join(sorted(VALID_CATEGORIES))}")
    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    slug = slugify(args.name)
    today = date.today().isoformat()
    out_path = LOCATIONS_DIR / f"{slug}.md"

    # Collision check
    if out_path.exists():
        print(f"ERROR: {out_path.relative_to(VAULT_ROOT)} already exists. Aborting.", file=sys.stderr)
        sys.exit(1)

    if not args.region:
        print(f"WARNING: No --region supplied. parent_region will be omitted from frontmatter.", file=sys.stderr)

    fantasy_name = getattr(args, "fantasy_name", "") or ""

    content = build_stub(
        name=args.name,
        slug=slug,
        lat=args.lat,
        lon=args.lon,
        category=args.category,
        fantasy_name=fantasy_name,
        description=args.description,
        region=args.region,
        visibility=args.visibility,
        today=today,
    )

    if args.dry_run:
        print(f"--- DRY RUN: would write {out_path.relative_to(VAULT_ROOT)} ---\n")
        print(content)
        return

    LOCATIONS_DIR.mkdir(parents=True, exist_ok=True)
    out_path.write_text(content, encoding="utf-8")
    print(f"Written: {out_path.relative_to(VAULT_ROOT)}")
    print(f"Slug:    {slug}")
    print()
    print("Next steps:")
    print("  1. python utilities/build.py geojson   # rebuild location GeoJSON")
    print("  2. python utilities/world/generate_map_workshop.py   # refresh workshop map")


if __name__ == "__main__":
    main()
