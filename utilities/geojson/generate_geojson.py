#!/usr/bin/env python3
"""
Generate world/data/tarim-shaiel-locations.geojson from location markdown files.

Replaces the hand-maintained GeoJSON file with a build artifact driven by the
markdown source-of-truth files in world/locations/*.md.

Usage:
    python utilities/geojson/generate_geojson.py [--public | --gm] [--out PATH]
    python utilities/build.py geojson [--public | --gm]
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    raise ImportError(
        "PyYAML is required (pip install -r requirements.txt, or check "
        "you're using the project's intended Python interpreter) — "
        "frontmatter parsing silently degrades to a broken minimal parser "
        "without it, producing empty/incorrect build output."
    )

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------

SCRIPT_DIR  = Path(__file__).parent
VAULT_ROOT  = SCRIPT_DIR.parent.parent

sys.path.insert(0, str(SCRIPT_DIR.parent))

from locations.location_parser import load_all_locations, LocationData
from shared.base_generator import make_generator

LOCATIONS_DIR = VAULT_ROOT / "world" / "locations"
OUTPUT_PATH   = VAULT_ROOT / "world" / "data" / "tarim-shaiel-locations.geojson"

# ---------------------------------------------------------------------------
# Icon / colour tables
# ---------------------------------------------------------------------------

# marker-color: keyed on frontmatter `mapmarker:` value
CATEGORY_COLORS: dict[str, str] = {
    "caravanserai":     "#D4A820",   # warm gold — waypoint/inn
    "capital":          "#8B6914",   # deep gold — major seat of power
    "city":             "#8B6914",   # deep gold — urban centre
    "fortress":         "#6B7280",   # steel grey — military
    "sacred-site":      "#F5F0E8",   # pale ivory — religious
    "ruins":            "#9CA3AF",   # light grey — abandoned
    "route-node":       "#A78040",   # muted gold-brown — road stop
    "water-body":       "#4A90D9",   # blue — water
    "landmark":         "#9CA3AF",   # neutral grey — geographic feature
    "mythic-landscape": "#C084FC",   # violet — cosmological
}
DEFAULT_COLOR = "#6B7280"

# marker-symbol: Maki icon names for MapLibre GL
MAKI_SYMBOLS: dict[str, str] = {
    "caravanserai":     "lodging",
    "capital":          "star",
    "city":             "town",
    "fortress":         "castle",
    "sacred-site":      "place-of-worship",
    "ruins":            "monument",
    "route-node":       "circle",
    "water-body":       "water",
    "landmark":         "mountain",
    "mythic-landscape": "star-stroked",
}
DEFAULT_SYMBOL = "circle"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_fm_extra(path: Path) -> dict:
    """Re-read frontmatter for fields not captured by LocationData (e.g. narrative_weight)."""
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL)
    if not m:
        return {}
    if _YAML_AVAILABLE:
        try:
            return yaml.safe_load(m.group(1)) or {}
        except Exception:
            return {}
    # Minimal fallback — handles simple scalar values only
    result: dict = {}
    for line in m.group(1).splitlines():
        kv = line.split(":", 1)
        if len(kv) == 2 and not line.startswith((" ", "-")):
            result[kv[0].strip()] = kv[1].strip().strip("'\"")
    return result


def _popup_html(loc: LocationData) -> str:
    """Assemble a small HTML snippet for map popups."""
    parts: list[str] = []
    if loc["description"]:
        parts.append(f"<p>{loc['description']}</p>")
    if loc["factions_visible"]:
        parts.append(
            f'<p class="popup-factions"><em>Factions:</em> '
            f'{", ".join(loc["factions_visible"])}</p>'
        )
    if loc["resources"]:
        parts.append(
            f'<p class="popup-resources"><em>Resources:</em> '
            f'{", ".join(loc["resources"])}</p>'
        )
    return "".join(parts)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate tarim-shaiel-locations.geojson from location markdown files."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--public", action="store_true",
        help="Public mode: include only visibility=public features"
    )
    mode.add_argument(
        "--gm", action="store_true",
        help="GM mode: include all features regardless of visibility"
    )
    parser.add_argument(
        "--out", default=str(OUTPUT_PATH),
        help="Override output path (default: world/data/tarim-shaiel-locations.geojson)"
    )
    args = parser.parse_args()

    public_only = args.public   # --gm and default both include everything
    out_path    = Path(args.out)
    mode_label  = "public" if public_only else ("gm" if args.gm else "all")

    def _rel(p: Path) -> str:
        try:
            return str(p.relative_to(VAULT_ROOT))
        except ValueError:
            return str(p)

    print(f"  Mode     : {mode_label}")
    print(f"  Source   : {_rel(LOCATIONS_DIR)}")
    print(f"  Output   : {_rel(out_path)}")

    # Parse all location files via the shared parser
    locations = load_all_locations(LOCATIONS_DIR, public_only=public_only)

    features: list[dict]      = []
    skipped:  list[tuple[str, str]] = []   # (slug, reason)
    seen_slugs: dict[str, str] = {}

    for loc in locations:
        slug = loc["slug"]

        # Duplicate slug check — hard error
        if slug in seen_slugs:
            print(
                f"  ERROR: duplicate slug '{slug}' in {loc['source_path']} "
                f"and {seen_slugs[slug]}",
                file=sys.stderr,
            )
            return 1
        seen_slugs[slug] = str(loc["source_path"])

        # Coordinates are required for a map feature
        if loc["lat"] is None or loc["lon"] is None:
            skipped.append((slug, "no coordinates"))
            continue

        if not loc["description"]:
            print(f"  WARN: {slug} has no description", file=sys.stderr)

        # Extra frontmatter fields not captured by location_parser
        fm_extra     = _read_fm_extra(loc["source_path"])
        narrative_wt = bool(fm_extra.get("narrative_weight"))

        mapmarker    = loc["mapmarker"]
        marker_color  = CATEGORY_COLORS.get(mapmarker, DEFAULT_COLOR)
        marker_symbol = MAKI_SYMBOLS.get(mapmarker, DEFAULT_SYMBOL)
        marker_size   = "large" if narrative_wt else "medium"

        features.append({
            "type": "Feature",
            "id": f"location_{slug}",
            "properties": {
                # Core identity
                "kind":         "location",
                "category":     loc["location_type"],   # matches existing consumer field
                "slug":         slug,
                "label":        loc["fantasy_name"] or loc["title"],
                "title":        loc["title"],
                "fantasy_name": loc["fantasy_name"],
                "description":  loc["description"],
                "visibility":   loc["visibility"],
                # Map styling
                "mapmarker":      mapmarker,
                "marker-symbol":  marker_symbol,
                "marker-color":   marker_color,
                "marker-size":    marker_size,
                # Rich data
                "factions":   loc["factions_visible"],
                "resources":  loc["resources"],
                "popup_html": _popup_html(loc),
                "url":        f"/locations/{slug}.html",
            },
            "geometry": {
                "type": "Point",
                # GeoJSON is [lon, lat]; location_parser already stores lat/lon separately
                "coordinates": [loc["lon"], loc["lat"]],
            },
        })

    geojson: dict = {"type": "FeatureCollection", "features": features}

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(geojson, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"  Generated: {len(features)} features written to {out_path.name}")
    if skipped:
        print(f"  Skipped  : {len(skipped)} location(s)")
        for s_slug, s_reason in skipped:
            print(f"             - {s_slug} ({s_reason})")

    return 0


# ---------------------------------------------------------------------------
# Generator protocol wrapper
# ---------------------------------------------------------------------------

generator = make_generator(
    "geojson",
    "Generate tarim-shaiel-locations.geojson from location markdown files",
    main,
)

if __name__ == "__main__":
    sys.exit(main())
