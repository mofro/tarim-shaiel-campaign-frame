#!/usr/bin/env python3
"""
Locations HTML Generator
=========================
Generates player-facing and GM location pages for the Tarim-Shaiel campaign.

Output structure:
  docs/world.html                         — world home page (full Leaflet map + region/location index)
  docs/locations/<slug>.html              — individual location detail pages
  docs/locations/regions/<slug>.html      — regional index pages

Usage:
    python utilities/locations/generate_locations_html.py
    python utilities/locations/generate_locations_html.py --public
    python utilities/locations/generate_locations_html.py --gm
    python utilities/locations/generate_locations_html.py --dry-run

Visibility gating (fails closed):
  --public: only `visibility: public` locations and all regions
  --gm    : all locations with GM callouts rendered; sets TS_GM_MODE=1
  default : same as --public (safe default)
"""

import json
import os
import sys
import argparse
from pathlib import Path
from html import escape

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent
DOCS_DIR   = VAULT_ROOT / "docs"

sys.path.insert(0, str(SCRIPT_DIR.parent))

from locations.location_parser import load_all_locations, LocationData
from locations.region_parser import load_all_regions, RegionData
from locations.location_components import (
    render_danger_pips,
    render_stats_row,
    render_faction_table,
    render_resources,
    render_mini_map,
    render_xref_stub,
    _TYPE_LABELS,
    MAP_ATTRIBUTION_HTML,
)
from shared.renderer import render_page
from shared.html_render import render_body

_LOCATIONS_DIR = VAULT_ROOT / "world" / "locations"
_REGIONS_DIR   = VAULT_ROOT / "world" / "regions"
_DATA_DIR      = VAULT_ROOT / "world" / "data"

_LOCATIONS_GEOJSON = _DATA_DIR / "tarim-shaiel-locations.geojson"
_ROUTES_GEOJSON    = _DATA_DIR / "tarim-shaiel-routes.geojson"
_REGIONS_GEOJSON   = _DATA_DIR / "tarim-shaiel-regions.geojson"

_GM_PAGE_BANNER = (
    '<div class="gm-page-banner">'
    'GM ARCHIVE — NOT FOR PLAYER DISTRIBUTION'
    '</div>\n'
)

# Tile URL constants are defined in location_components.py and imported above.

# ---------------------------------------------------------------------------
# GeoJSON loading
# ---------------------------------------------------------------------------

def _load_geojson(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        print(f"  WARNING: could not load {path.name}: {e}", file=sys.stderr)
        return None


def _filter_geojson_public(geojson: dict | None) -> dict | None:
    """Remove features with visibility:secret for public builds."""
    if not geojson:
        return geojson
    public_features = [
        f for f in geojson.get('features', [])
        if f.get('properties', {}).get('visibility') != 'secret'
    ]
    return {**geojson, 'features': public_features}


# ---------------------------------------------------------------------------
# World home map
# ---------------------------------------------------------------------------


def _build_world_map_html(
    locations: list[LocationData],
    locations_geojson: dict | None,
    routes_geojson: dict | None,
    regions_geojson: dict | None,
) -> str:
    """Build the full-page Leaflet map for world.html."""

    # Build location popup data keyed by slug
    popup_map: dict[str, dict] = {}
    for loc in locations:
        popup_map[loc['slug']] = {
            'title': loc['title'],
            'type':  _TYPE_LABELS.get(loc['location_type'], loc['location_type']),
            'url':   f'/locations/{loc["slug"]}.html',
        }

    # Inline GeoJSON and popup data as JS variables
    data_js = f'var _locPopups = {json.dumps(popup_map)};\n'
    sources_js = ''
    layers_js = ''

    if regions_geojson:
        data_js += f'var _regionGJ = {json.dumps(regions_geojson)};\n'
        sources_js += 'map.addSource("regions", {type:"geojson", data:_regionGJ});\n'
        layers_js += (
            'map.addLayer({id:"regions-fill",type:"fill",source:"regions",'
            'paint:{"fill-color":["coalesce",["get","fill"],"#b8892a"],"fill-opacity":0.08}});\n'
            'map.addLayer({id:"regions-line",type:"line",source:"regions",'
            'paint:{"line-color":["coalesce",["get","stroke"],"#b8892a"],"line-width":2}});\n'
        )
    if routes_geojson:
        data_js += f'var _routeGJ = {json.dumps(routes_geojson)};\n'
        sources_js += 'map.addSource("routes", {type:"geojson", data:_routeGJ});\n'
        layers_js += (
            'map.addLayer({id:"routes",type:"line",source:"routes",'
            'layout:{"line-cap":"butt"},'
            'paint:{"line-color":"#b8892a","line-width":1.5,"line-opacity":0.5,"line-dasharray":[4,4]}});\n'
        )
    if locations_geojson:
        data_js += f'var _locGJ = {json.dumps(locations_geojson)};\n'
        sources_js += 'map.addSource("locations", {type:"geojson", data:_locGJ});\n'
        layers_js += (
            'map.addLayer({id:"locations",type:"circle",source:"locations",'
            'paint:{"circle-radius":6,"circle-color":"#f5edd8","circle-stroke-width":2,"circle-stroke-color":"#7a1f1f","circle-opacity":0.9}});\n'
            'map.on("click","locations",function(e){\n'
            '  var slug=String(e.features[0].id||"").replace("location_","");\n'
            '  var info=_locPopups[slug]||{title:String(e.features[0].id),type:"",url:"#"};\n'
            '  new maplibregl.Popup().setLngLat(e.features[0].geometry.coordinates)\n'
            '    .setHTML("<strong>"+info.title+"</strong><br>"+info.type+"<br><a href=\'"+info.url+"\'>View →</a>")\n'
            '    .addTo(map);\n'
            '});\n'
            'map.on("mouseenter","locations",function(){map.getCanvas().style.cursor="pointer";});\n'
            'map.on("mouseleave","locations",function(){map.getCanvas().style.cursor="";});\n'
        )

    return f"""<div id="world-map"></div>
<script>
(function() {{
  {data_js}
  var map = new maplibregl.Map({{
    container: 'world-map',
    style: '/assets/map-style.json',
    center: [75.0, 40.0],
    zoom: 5,
    maxZoom: 8
  }});
  map.on('load', function() {{
    {sources_js}
    {layers_js}
  }});
}})();
</script>
"""


# ---------------------------------------------------------------------------
# Location detail page
# ---------------------------------------------------------------------------

def _build_location_page(
    loc: LocationData,
    regions: dict[str, RegionData],
    locations_geojson: dict | None,
    routes_geojson: dict | None,
    gm_mode: bool,
) -> str:
    region = regions.get(loc['parent_region']) if loc['parent_region'] else None
    revealed = set(loc['gm_revealed'])

    body_html, _ = render_body(
        loc['body'],
        vault=VAULT_ROOT,
        docs=DOCS_DIR,
        gm_mode=gm_mode,
        revealed_ids=revealed,
    )

    mini_map_html = render_mini_map(loc, locations_geojson, routes_geojson, zoom=7)
    stats_row_html = render_stats_row(loc, region)
    danger_html = render_danger_pips(loc['location_type'])
    faction_html = render_faction_table(loc['factions_visible'])
    resources_html = render_resources(loc['resources'])
    xref_html = render_xref_stub()

    gm_banner = _GM_PAGE_BANNER if gm_mode else ''

    return render_page(
        'pages/location-detail.html',
        title=loc['title'],
        fantasy_name=loc['fantasy_name'],
        description=loc['description'],
        location_type=loc['location_type'],
        location_type_label=_TYPE_LABELS.get(loc['location_type'], loc['location_type'].replace('-', ' ').title()),
        visibility=loc['visibility'],
        stats_row_html=stats_row_html,
        danger_pips_html=danger_html,
        mini_map_html=mini_map_html,
        content_html=body_html,
        faction_table_html=faction_html,
        resources_html=resources_html,
        xref_html=xref_html,
        region_title=region['title'] if region else None,
        region_slug=loc['parent_region'] if loc['parent_region'] else '',
        gm_page_banner_html=gm_banner,
        gm_mode=gm_mode,
        extra_css=['world-location'],
        generator_name='generate_locations_html.py',
    )


# ---------------------------------------------------------------------------
# Region index page
# ---------------------------------------------------------------------------

def _build_region_page(
    region: RegionData,
    region_locations: list[LocationData],
    locations_geojson: dict | None,
    routes_geojson: dict | None,
    gm_mode: bool,
) -> str:
    from shared.html_render import render_body as _rb
    body_html, _ = _rb(region['body'], vault=VAULT_ROOT, docs=DOCS_DIR, gm_mode=gm_mode)

    # Region mini-map centred on the first location with coords
    region_map_html = ''
    anchor = next((l for l in region_locations if l['lat'] is not None), None)
    if anchor:
        from locations.location_components import render_mini_map
        region_map_html = render_mini_map(anchor, locations_geojson, routes_geojson, zoom=5)

    # Location cards
    loc_cards = []
    for l in region_locations:
        loc_cards.append({
            'slug': l['slug'],
            'title': l['title'],
            'description': l['description'],
            'location_type': l['location_type'],
            'location_type_label': _TYPE_LABELS.get(l['location_type'], l['location_type']),
            'danger_pips_html': render_danger_pips(l['location_type']),
        })

    return render_page(
        'pages/region-index.html',
        title=region['title'],
        location_count=len(region_locations),
        primary_ancestry=region['primary_ancestry'],
        faction_weight=region['faction_weight'],
        region_map_html=region_map_html,
        content_html=body_html,
        locations=loc_cards,
        gm_mode=gm_mode,
        extra_css=['world-location', 'world-region'],
        generator_name='generate_locations_html.py',
    )


# ---------------------------------------------------------------------------
# World home page
# ---------------------------------------------------------------------------

def _build_world_home(
    locations: list[LocationData],
    regions: dict[str, RegionData],
    locations_geojson: dict | None,
    routes_geojson: dict | None,
    regions_geojson: dict | None,
    gm_mode: bool,
) -> str:
    world_map_html = _build_world_map_html(
        locations, locations_geojson, routes_geojson, regions_geojson
    )

    region_list = []
    for slug, r in sorted(regions.items()):
        region_list.append({
            'slug': r['slug'],
            'title': r['title'],
            'location_count': sum(1 for l in locations if l['parent_region'] == slug),
            'primary_ancestry': r['primary_ancestry'],
            'faction_weight': r['faction_weight'],
        })

    all_locations_sorted = sorted(locations, key=lambda l: l['title'])
    az_list = [{
        'slug': l['slug'],
        'title': l['title'],
        'location_type': l['location_type'],
        'location_type_label': _TYPE_LABELS.get(l['location_type'], l['location_type']),
    } for l in all_locations_sorted]

    return render_page(
        'pages/world-home.html',
        title='Tarim-Shaiel — World Map',
        world_map_html=world_map_html,
        regions=region_list,
        all_locations=az_list,
        gm_mode=gm_mode,
        extra_css=['world-map'],
        generator_name='generate_locations_html.py',
    )


# ---------------------------------------------------------------------------
# Main generation loop
# ---------------------------------------------------------------------------

def generate(
    public_only: bool = True,
    gm_mode: bool = False,
    dry_run: bool = False,
) -> int:
    if gm_mode:
        os.environ['TS_GM_MODE'] = '1'
        public_only = False

    locations = load_all_locations(_LOCATIONS_DIR, public_only=public_only)
    regions   = load_all_regions(_REGIONS_DIR)

    locs_gj   = _load_geojson(_LOCATIONS_GEOJSON)
    routes_gj = _load_geojson(_ROUTES_GEOJSON)
    regions_gj = _load_geojson(_REGIONS_GEOJSON)

    if public_only:
        locs_gj = _filter_geojson_public(locs_gj)

    print(f"  Loaded {len(locations)} locations, {len(regions)} regions")

    errors: list[str] = []

    # --- Location detail pages ---
    locs_out = DOCS_DIR / "locations"
    if not dry_run:
        locs_out.mkdir(parents=True, exist_ok=True)

    for loc in locations:
        try:
            html = _build_location_page(loc, regions, locs_gj, routes_gj, gm_mode)
        except Exception as e:
            msg = f"  ERROR building {loc['slug']}: {e}"
            print(msg, file=sys.stderr)
            errors.append(msg)
            continue

        out_path = locs_out / f"{loc['slug']}.html"
        if dry_run:
            print(f"  [DRY] would write {out_path.relative_to(VAULT_ROOT)}")
        else:
            out_path.write_text(html, encoding='utf-8')

    print(f"  Location pages: {len(locations)}")

    # --- Region index pages ---
    regions_out = locs_out / "regions"
    if not dry_run:
        regions_out.mkdir(parents=True, exist_ok=True)

    for slug, region in regions.items():
        region_locs = [l for l in locations if l['parent_region'] == slug]
        try:
            html = _build_region_page(region, region_locs, locs_gj, routes_gj, gm_mode)
        except Exception as e:
            msg = f"  ERROR building region {slug}: {e}"
            print(msg, file=sys.stderr)
            errors.append(msg)
            continue

        out_path = regions_out / f"{slug}.html"
        if dry_run:
            print(f"  [DRY] would write {out_path.relative_to(VAULT_ROOT)}")
        else:
            out_path.write_text(html, encoding='utf-8')

    print(f"  Region pages: {len(regions)}")

    # --- World home ---
    try:
        world_html = _build_world_home(
            locations, regions, locs_gj, routes_gj, regions_gj, gm_mode
        )
    except Exception as e:
        msg = f"  ERROR building world.html: {e}"
        print(msg, file=sys.stderr)
        errors.append(msg)
        world_html = None

    if world_html:
        out_path = DOCS_DIR / "world.html"
        if dry_run:
            print(f"  [DRY] would write {out_path.relative_to(VAULT_ROOT)}")
        else:
            out_path.write_text(world_html, encoding='utf-8')
        print("  World home: docs/world.html")

    if errors:
        print(f"\n  {len(errors)} error(s) during generation.")
        return 1
    return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate HTML for world locations, regions, and world home page."
    )
    parser.add_argument('--public', action='store_true',
                        help='Only include visibility:public locations (default behaviour)')
    parser.add_argument('--gm', action='store_true',
                        help='GM mode: include all locations, render GM callouts')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show output paths without writing files')
    args = parser.parse_args()

    return generate(
        public_only=not args.gm,
        gm_mode=args.gm,
        dry_run=args.dry_run,
    )


# ---------------------------------------------------------------------------
# Generator protocol wrapper (for build.py registry)
# ---------------------------------------------------------------------------
from shared.base_generator import make_generator
generator = make_generator(
    "locations",
    "Location detail pages, region indexes, and world home map",
    main,
)


if __name__ == "__main__":
    sys.exit(main())
