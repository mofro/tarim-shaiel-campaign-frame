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
    MAPTILER_STYLE_URL,
)
from locations.map_icons import icon_registration_js
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



def _build_locations_geojson(locations: list[LocationData]) -> dict:
    """Build a GeoJSON FeatureCollection from parsed LocationData.

    Regenerated on every build — markdown files are the source of truth.
    Only includes locations that have coordinates.
    """
    features = []
    for loc in locations:
        if loc['lat'] is None or loc['lon'] is None:
            continue
        features.append({
            'type': 'Feature',
            'id': f'location_{loc["slug"]}',
            'properties': {
                'kind': 'location',
                'category': loc['location_type'],
                'label': loc['fantasy_name'] or loc['title'],
                'title': loc['title'],
                'description': loc['description'],
                'fantasyName': loc['fantasy_name'],
                'visibility': loc['visibility'],
                'mapLabel': loc['map_label'],
                'mapMarker': loc['map_marker'],
                'slug': loc['slug'],
            },
            'geometry': {
                'type': 'Point',
                'coordinates': [loc['lon'], loc['lat']],
            },
        })
    return {'type': 'FeatureCollection', 'features': features}


def _filter_geojson_public(geojson: dict | None) -> dict | None:
    """Remove gm_secrets features for public builds."""
    if not geojson:
        return geojson
    public_features = [
        f for f in geojson.get('features', [])
        if f.get('properties', {}).get('visibility') != 'gm_secrets'
    ]
    return {**geojson, 'features': public_features}


# ---------------------------------------------------------------------------
# Shared icon registration JS (used by world home and mini-maps)
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# World home map
# ---------------------------------------------------------------------------


def _locations_layers_js(gm_mode: bool = False) -> str:
    """Return JS that adds four zoom-tiered symbol layers for locations.

    Each tier entry: (layer_id, categories, minzoom, fade_start, fade_end,
                      label_font, label_size)

    label_font=None means no labels for that tier.
    In gm_mode, each layer filters out gm_secrets so they don't overlap the
    dedicated dim layers added by _gm_secrets_layers_js().
    """
    # mapMarker frontmatter override takes priority over the category-driven
    # icon: a string -> "cat-<string>" directly, unset/null -> the category
    # match. false (no icon) is handled by excluding the feature via filter
    # below, not here -- MapLibre's style spec forbids nesting a zoom-based
    # interpolate (used for icon-opacity's fade) inside a "case", so hiding
    # via opacity isn't legal; filtering the feature out entirely is.
    icon_match = (
        '"icon-image":["case",'
        '["!=",["get","mapMarker"],null],["concat","cat-",["get","mapMarker"]],'
        '["match",["get","category"],'
        '"city","cat-city",'
        '"caravanserai","cat-route-node",'
        '"chokepoint","cat-fortress",'
        '"mountain-pass","cat-landmark",'
        '"oasis","cat-oasis",'
        '"power-site","cat-sacred-site",'
        '"route-node","cat-route-node",'
        '"ruins","cat-dungeon",'
        '"sacred-site","cat-sacred-site",'
        '"site","cat-poi",'
        '"cat-poi"]],'
        '"icon-size":1.3,"icon-allow-overlap":true,"icon-anchor":"center"'
    )

    # fmt: off
    tiers = [
        # layer_id               categories                                  mz  fs   fe  font                                      size
        ('locations-major',     ['city', 'landmark', 'fortress'],            3,  3.5, 4,  ['Roboto Serif Regular', 'Noto Sans Bold'],  15),
        ('locations-secondary', ['sacred-site', 'oasis', 'caravanserai'],    5,  5.5, 6,  ['Roboto Serif Regular', 'Noto Sans Italic'], 13),
        ('locations-routes',    ['route-node', 'chokepoint', 'mountain-pass'],6, 6.5, 7,  None,                                     0),
        ('locations-detail',    ['ruins', 'poi', 'power-site', 'site'],      7,  7.5, 8,  None,                                     0),
    ]
    # fmt: on

    js = ''
    layer_ids = []
    for layer_id, cats, minzoom, fade_start, fade_end, label_font, label_size in tiers:
        cats_json = str(cats).replace("'", '"')
        opacity_expr = f'["interpolate",["linear"],["zoom"],{fade_start},0,{fade_end},0.95]'

        if label_font:
            font_json = str(label_font).replace("'", '"')
            label_layout = (
                f',"text-field":["case",["==",["get","mapLabel"],false],"",["get","label"]]'
                f',"text-font":{font_json}'
                f',"text-size":{label_size}'
                f',"text-offset":[0,1.1]'
                f',"text-anchor":"top"'
                f',"text-max-width":8'
                f',"text-letter-spacing":0.03'
                f',"text-allow-overlap":false'
            )
            label_paint = (
                f',"text-color":"#ffffff"'
                f',"text-halo-color":"rgba(10,8,5,0.95)"'
                f',"text-halo-width":2'
                f',"text-opacity":{opacity_expr}'
            )
        else:
            label_layout = ''
            label_paint = ''

        cat_filter = f'["all",["match",["get","category"],{cats_json},true,false],["!=",["get","mapMarker"],false]]'
        if gm_mode:
            layer_filter = f'["all",{cat_filter},["!=",["get","visibility"],"gm_secrets"]]'
        else:
            layer_filter = cat_filter
        js += (
            f'map.addLayer({{id:"{layer_id}",type:"symbol",minzoom:{minzoom},source:"locations",'
            f'filter:{layer_filter},'
            f'layout:{{{icon_match}{label_layout}}},'
            f'paint:{{"icon-opacity":{opacity_expr}{label_paint}}}}});\n'
        )
        layer_ids.append(layer_id)

    # Shared popup hover + click-to-navigate handlers across all tiers
    ids_js = str(layer_ids).replace("'", '"')
    js += (
        'var _hoverPopup=new maplibregl.Popup({className:"ts-map-popup",offset:12,closeButton:false,closeOnClick:false});\n'
        f'{ids_js}.forEach(function(lyr){{\n'
        '  map.on("mouseenter",lyr,function(e){\n'
        '    map.getCanvas().style.cursor="pointer";\n'
        '    var slug=e.features[0].properties._slug||"";\n'
        '    var info=_locPopups[slug]||{title:e.features[0].properties.title||slug,type:"",url:"#"};\n'
        '    var html="<div class=\'ts-popup\'>"\n'
        '      +"<div class=\'ts-popup__title\'>"+info.title+"</div>"\n'
        '      +(info.type?"<div class=\'ts-popup__type\'>"+info.type+"</div>":"")\n'
        '      +"</div>";\n'
        '    _hoverPopup.setLngLat(e.features[0].geometry.coordinates).setHTML(html).addTo(map);\n'
        '  });\n'
        '  map.on("mouseleave",lyr,function(){\n'
        '    map.getCanvas().style.cursor="";\n'
        '    _hoverPopup.remove();\n'
        '  });\n'
        '  map.on("click",lyr,function(e){\n'
        '    var slug=e.features[0].properties._slug||"";\n'
        '    var info=_locPopups[slug]||{};\n'
        '    if(info.url&&info.url!="#")window.location.href=info.url;\n'
        '  });\n'
        '});\n'
    )
    return js


def _gm_secrets_layers_js() -> str:
    """Return JS adding dimmed symbol layers for gm_secrets features (GM build only).

    Mirrors the four tiers in _locations_layers_js() but filtered to
    visibility==gm_secrets and rendered at 40% opacity so the GM can
    distinguish secret vs revealed at a glance.
    """
    # fmt: off
    tiers = [
        ('gm-locations-major',     ['city', 'landmark', 'fortress'],             3,  3.5, 4),
        ('gm-locations-secondary', ['sacred-site', 'oasis', 'caravanserai'],     5,  5.5, 6),
        ('gm-locations-routes',    ['route-node', 'chokepoint', 'mountain-pass'],6,  6.5, 7),
        ('gm-locations-detail',    ['ruins', 'poi', 'power-site', 'site'],       7,  7.5, 8),
    ]
    # fmt: on

    # mapMarker frontmatter override takes priority over the category-driven
    # icon: a string -> "cat-<string>" directly, unset/null -> the category
    # match. false (no icon) is handled via filter exclusion below, not here
    # — see the comment in _locations_layers_js for why.
    icon_match = (
        '"icon-image":["case",'
        '["!=",["get","mapMarker"],null],["concat","cat-",["get","mapMarker"]],'
        '["match",["get","category"],'
        '"city","cat-city",'
        '"caravanserai","cat-route-node",'
        '"chokepoint","cat-fortress",'
        '"mountain-pass","cat-landmark",'
        '"oasis","cat-oasis",'
        '"power-site","cat-sacred-site",'
        '"route-node","cat-route-node",'
        '"ruins","cat-dungeon",'
        '"sacred-site","cat-sacred-site",'
        '"site","cat-poi",'
        '"cat-poi"]],'
        '"icon-size":1.3,"icon-allow-overlap":true,"icon-anchor":"center"'
    )

    js = ''
    gm_layer_ids = []
    for layer_id, cats, minzoom, fade_start, fade_end in tiers:
        cats_json = str(cats).replace("'", '"')
        # Fade in to 0.4 (not 0.95) — visually distinct from public markers
        opacity_expr = f'["interpolate",["linear"],["zoom"],{fade_start},0,{fade_end},0.4]'
        layer_filter = (
            f'["all",["match",["get","category"],{cats_json},true,false],'
            f'["!=",["get","mapMarker"],false],'
            f'["==",["get","visibility"],"gm_secrets"]]'
        )
        js += (
            f'map.addLayer({{id:"{layer_id}",type:"symbol",minzoom:{minzoom},source:"locations",'
            f'filter:{layer_filter},'
            f'layout:{{{icon_match}}},'
            f'paint:{{"icon-opacity":{opacity_expr}}}}});\n'
        )
        gm_layer_ids.append(layer_id)

    # Hover popup labels GM-only features; click navigates same as public
    ids_js = str(gm_layer_ids).replace("'", '"')
    js += (
        f'{ids_js}.forEach(function(lyr){{\n'
        '  map.on("mouseenter",lyr,function(e){\n'
        '    map.getCanvas().style.cursor="pointer";\n'
        '    var slug=e.features[0].properties._slug||"";\n'
        '    var info=_locPopups[slug]||{title:e.features[0].properties.title||slug,type:"",url:"#"};\n'
        '    var html="<div class=\'ts-popup\'>"\n'
        '      +"<div class=\'ts-popup__title\'>"+info.title+"</div>"\n'
        '      +"<div class=\'ts-popup__type gm-secret-badge\'>GM only</div>"\n'
        '      +(info.type?"<div class=\'ts-popup__type\'>"+info.type+"</div>":"")\n'
        '      +"</div>";\n'
        '    _hoverPopup.setLngLat(e.features[0].geometry.coordinates).setHTML(html).addTo(map);\n'
        '  });\n'
        '  map.on("mouseleave",lyr,function(){\n'
        '    map.getCanvas().style.cursor="";\n'
        '    _hoverPopup.remove();\n'
        '  });\n'
        '  map.on("click",lyr,function(e){\n'
        '    var slug=e.features[0].properties._slug||"";\n'
        '    var info=_locPopups[slug]||{};\n'
        '    if(info.url&&info.url!="#")window.location.href=info.url;\n'
        '  });\n'
        '});\n'
    )
    return js


def _build_world_map_html(
    locations: list[LocationData],
    locations_geojson: dict | None,
    routes_geojson: dict | None,
    regions_geojson: dict | None,
    gm_mode: bool = False,
    show_locations: bool = False,
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
            'map.addLayer({id:"regions-fill",type:"fill",minzoom:2,source:"regions",'
            'paint:{"fill-color":["coalesce",["get","fill"],"#b8892a"],'
            '"fill-opacity":["interpolate",["linear"],["zoom"],3,0.08,7,0]}});\n'
            'map.addLayer({id:"regions-line",type:"line",minzoom:2,source:"regions",'
            'paint:{"line-color":["coalesce",["get","stroke"],"#b8892a"],"line-width":2,'
            '"line-opacity":["interpolate",["linear"],["zoom"],3,0.7,7,0]}});\n'
        )
    if routes_geojson:
        data_js += f'var _routeGJ = {json.dumps(routes_geojson)};\n'
        sources_js += 'map.addSource("routes", {type:"geojson", data:_routeGJ});\n'
        layers_js += (
            'map.addLayer({id:"routes",type:"line",minzoom:4,source:"routes",'
            'layout:{"line-cap":"butt"},'
            'paint:{"line-color":"#b8892a","line-width":1.5,"line-opacity":0.5,"line-dasharray":[4,4]}});\n'
        )
    if locations_geojson and show_locations:
        # Inject _slug into each feature's properties so the click handler
        # can look up popup data by slug without relying on MapLibre feature IDs.
        enriched_features = []
        for feat in locations_geojson.get('features', []):
            slug = str(feat.get('id', '')).replace('location_', '')
            enriched_features.append({
                **feat,
                'properties': {**feat.get('properties', {}), '_slug': slug}
            })
        enriched_loc_geojson = {**locations_geojson, 'features': enriched_features}
        data_js += f'var _locGJ = {json.dumps(enriched_loc_geojson)};\n'
        sources_js += 'map.addSource("locations", {type:"geojson", data:_locGJ});\n'
        layers_js += (
            icon_registration_js()
            + _locations_layers_js(gm_mode=gm_mode)
        )
        if gm_mode:
            layers_js += _gm_secrets_layers_js()

    # GM-only coordinate picker -- click the map to read off real lat/lng for
    # siting a new location. Entirely absent from public builds (not just
    # hidden): gm_mode is baked in at generation time, so the HTML/JS below
    # simply doesn't exist in the --public output.
    coord_picker_html = ''
    coord_picker_js = ''
    if gm_mode:
        coord_picker_html = (
            '<div id="coord-picker" '
            'style="position:absolute;bottom:10px;left:10px;z-index:5;'
            'background:rgba(10,8,5,0.85);color:#e8dcc4;font:12px monospace;'
            'padding:6px 10px;border-radius:3px;cursor:pointer;'
            'border:1px solid rgba(184,146,44,0.4);" '
            'title="Click the map to read coordinates. Click this readout to copy.">'
            'Click map for coordinates</div>'
        )
        coord_picker_js = (
            'var coordEl = document.getElementById("coord-picker");\n'
            'map.on("click", function(e) {\n'
            '  var lat = e.lngLat.lat.toFixed(6), lng = e.lngLat.lng.toFixed(6);\n'
            '  coordEl.dataset.coords = "  - " + lat + "\\n  - " + lng;\n'
            '  coordEl.textContent = "lat " + lat + ", lng " + lng + "  (click to copy)";\n'
            '});\n'
            'coordEl.addEventListener("click", function() {\n'
            '  if (!coordEl.dataset.coords) return;\n'
            '  navigator.clipboard.writeText(coordEl.dataset.coords).then(function() {\n'
            '    var prev = coordEl.textContent;\n'
            '    coordEl.textContent = "Copied!";\n'
            '    setTimeout(function() { coordEl.textContent = prev; }, 900);\n'
            '  });\n'
            '});\n'
        )

    # Public: fixed single zoom, non-zoomable (original design intent).
    # GM mode: real zoom range so the coordinate picker can be used precisely
    # -- one pixel at the fixed zoom 5 view is ~3.7km of real ground, far too
    # coarse for siting a new location.
    world_min_zoom = 3 if gm_mode else 5
    world_max_zoom = 14 if gm_mode else 5

    return f"""<div id="world-map-inner-wrap" style="position:relative;">
<div id="world-map"></div>
{coord_picker_html}
</div>
<script>
(function() {{
  {data_js}
  var map = window._tsMap = new maplibregl.Map({{
    container: 'world-map',
    style: '{MAPTILER_STYLE_URL}',
    center: [75.0, 40.0],
    zoom: 5,
    minZoom: {world_min_zoom},
    maxZoom: {world_max_zoom}
  }});
  {coord_picker_js}
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
        extra_css=['world-base', 'world-location'],
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
        extra_css=['world-base', 'world-location', 'world-region'],
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
        # Region boundary boxes disabled -- not ready for display yet.
        # Pass regions_geojson through again once they are.
        locations, locations_geojson, routes_geojson, None,
        gm_mode=gm_mode, show_locations=True,
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
        show_locations=True,
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

    locations  = load_all_locations(_LOCATIONS_DIR, public_only=False)
    regions    = load_all_regions(_REGIONS_DIR)

    # Build in-memory locations GeoJSON for HTML map rendering.
    # The file at world/data/tarim-shaiel-locations.geojson is owned by the
    # geojson generator (utilities/geojson/generate_geojson.py) — do not write it here.
    locs_gj = _build_locations_geojson(locations)

    routes_gj  = _load_geojson(_ROUTES_GEOJSON)
    regions_gj = _load_geojson(_REGIONS_GEOJSON)

    # Filter to public-only locations for public builds
    if public_only:
        locations = [l for l in locations if l['visibility'] != 'gm_secrets']
        locs_gj   = _filter_geojson_public(locs_gj)

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
