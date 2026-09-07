"""
Location HTML component renderers.

Each function takes structured data and returns an HTML fragment string.
Used by the main generator to assemble location detail pages.
"""

import json
import os
import sys
from html import escape
from pathlib import Path
from typing import Optional

from locations.location_parser import LocationData
from locations.region_parser import RegionData
from locations.map_icons import icon_registration_js


# ---------------------------------------------------------------------------
# Danger / tier pips
# ---------------------------------------------------------------------------

_DANGER_BY_TYPE: dict[str, int] = {
    "city": 1,
    "town": 1,
    "route-node": 2,
    "oasis": 2,
    "sacred-site": 3,
    "dungeon": 4,
    "landmark": 3,
    "fortress": 3,
    "poi": 1,
}

_TYPE_LABELS: dict[str, str] = {
    "city": "City",
    "town": "Town",
    "route-node": "Route Node",
    "oasis": "Oasis",
    "sacred-site": "Sacred Site",
    "dungeon": "Dungeon",
    "landmark": "Landmark",
    "fortress": "Fortress",
    "poi": "Point of Interest",
}


def render_danger_pips(location_type: str, count: Optional[int] = None) -> str:
    """Render filled/empty danger pips (1–5 scale)."""
    if count is None:
        count = _DANGER_BY_TYPE.get(location_type, 2)
    filled = "&#9679;" * count
    empty = "&#9675;" * (5 - count)
    return (
        f'<div class="danger-pips" title="Danger level {count}/5">'
        f'<span class="pips-filled">{filled}</span>'
        f'<span class="pips-empty">{empty}</span>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# Stats row (type + elevation + region)
# ---------------------------------------------------------------------------

def render_stats_row(loc: LocationData, region: Optional[RegionData] = None) -> str:
    """Render the stats badge strip beneath the location title."""
    type_label = _TYPE_LABELS.get(loc['location_type'], loc['location_type'].replace('-', ' ').title())
    parts = [f'<span class="stat-badge stat-badge--type">{escape(type_label)}</span>']

    if loc['elevation'] is not None and loc['elevation'] != 0:
        elev_m = loc['elevation']
        parts.append(f'<span class="stat-badge stat-badge--elevation">{elev_m:,} m</span>')

    if region:
        region_url = f'/locations/regions/{escape(region["slug"])}.html'
        parts.append(
            f'<span class="stat-badge stat-badge--region">'
            f'<a href="{region_url}">{escape(region["title"])}</a>'
            f'</span>'
        )
    elif loc['parent_region']:
        slug = str(loc['parent_region'])
        label = slug.replace('-', ' ').title()
        parts.append(
            f'<span class="stat-badge stat-badge--region">'
            f'<a href="/locations/regions/{escape(slug)}.html">{escape(label)}</a>'
            f'</span>'
        )

    return f'<div class="stats-row">{"".join(parts)}</div>\n'


# ---------------------------------------------------------------------------
# Faction table
# ---------------------------------------------------------------------------

def render_faction_table(factions: list[str]) -> str:
    """Render visible factions as a compact table."""
    if not factions:
        return ''

    rows = ''.join(
        f'<tr><td>{escape(f)}</td></tr>\n'
        for f in factions
    )
    return (
        f'<div class="faction-table">\n'
        f'  <h3 class="faction-table__heading">Factions Present</h3>\n'
        f'  <table>\n{rows}  </table>\n'
        f'</div>\n'
    )


# ---------------------------------------------------------------------------
# Resources list
# ---------------------------------------------------------------------------

def render_resources(resources: list[str]) -> str:
    """Render resource badges."""
    if not resources:
        return ''
    badges = ''.join(
        f'<span class="resource-badge">{escape(r)}</span>'
        for r in resources
    )
    return f'<div class="resources-list">{badges}</div>\n'


# ---------------------------------------------------------------------------
# MapLibre GL JS map configuration
# The style id itself isn't sensitive, but the MapTiler key is -- it must
# come from the environment (Netlify env var in production, exported locally
# for dev builds) rather than being committed to source. See
# https://github.com/mofro/tarim-shaiel-campaign-frame/issues/275
# ---------------------------------------------------------------------------

def _load_dotenv() -> None:
    """Fill os.environ from a repo-root .env file, if one exists.

    Real environment variables always win -- this only uses setdefault, so a
    shell export or Netlify's actual env var is never overridden by .env.
    No new dependency: .env files are simple enough not to need one.
    """
    env_path = Path(__file__).resolve().parent.parent.parent / '.env'
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, _, value = line.partition('=')
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


_load_dotenv()

MAPTILER_STYLE_ID = '01a074c7-536a-71cb-b0d8-9e7fe4fd1100'  # topo-tarim-copy (clean topo, no roads)
# MAPTILER_STYLE_ID = '019e13d9-26c8-7cd9-bf8d-64d83f66624e'  # custom campaign style
MAPTILER_KEY = os.environ.get('MAPTILER_KEY', '')
if not MAPTILER_KEY:
    print(
        "WARNING: MAPTILER_KEY environment variable is not set -- "
        "maps will fail to load tiles. Set it in your shell for local "
        "builds, or in Netlify's Environment Variables for production.",
        file=sys.stderr,
    )
MAPTILER_STYLE_URL = (
    f'https://api.maptiler.com/maps/{MAPTILER_STYLE_ID}/style.json?key={MAPTILER_KEY}'
)

# Attribution shown below non-interactive mini-maps (world map uses built-in
# MapLibre attribution control which reads from the style JSON).
MAP_ATTRIBUTION_HTML = (
    '<div class="map-attribution">'
    'Map &copy; <a href="https://www.maptiler.com/" target="_blank" rel="noopener">MapTiler</a> / '
    '<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OSM</a>'
    '</div>'
)


# Mirrors the tier structure in generate_locations_html.py::_locations_layers_js
# (same category groupings + zoom thresholds) so mini-maps and the world map
# reveal locations the same way as you zoom. Duplicated rather than imported —
# generate_locations_html.py imports FROM this module, so importing back would
# create a circular dependency.
_MINI_MAP_TIERS = [
    # layer_id            categories                                    mz  fs   fe   label_font                                     size
    ('mm-locations-major',     ['city', 'landmark', 'fortress'],             3, 3.5, 4,  ['Roboto Serif Regular', 'Noto Sans Bold'],   12),
    ('mm-locations-towns',     ['town'],                                      4, 4.5, 5,  ['Roboto Serif Regular', 'Noto Sans Regular'], 11),
    ('mm-locations-secondary', ['sacred-site', 'oasis', 'caravanserai'],     5, 5.5, 6,  ['Roboto Serif Regular', 'Noto Sans Italic'], 11),
    ('mm-locations-routes',    ['route-node', 'chokepoint', 'mountain-pass'],6, 6.5, 7,  None,                                       0),
    ('mm-locations-detail',    ['ruins', 'poi', 'power-site', 'site'],       7, 7.5, 8,  None,                                       0),
]


def _mini_map_icon_match() -> str:
    # mapMarker frontmatter override takes priority: a string -> "cat-<string>"
    # directly, unset/null -> the category-driven match below. false (no icon)
    # is handled via filter exclusion in _mini_map_tiered_layers_js, not here —
    # MapLibre's style spec forbids nesting a zoom-based interpolate (used for
    # icon-opacity's fade) inside a "case" expression, so hiding via opacity
    # isn't legal; filtering the feature out of the layer entirely is.
    return (
        '["case",'
        '["!=",["get","mapMarker"],null],["concat","cat-",["get","mapMarker"]],'
        '["match",["get","category"],'
        '"city","cat-city","capital","cat-capital","town","cat-town","caravanserai","cat-route-node",'
        '"fortress","cat-fortress","chokepoint","cat-fortress",'
        '"landmark","cat-landmark","mountain-pass","cat-landmark",'
        '"oasis","cat-oasis","Oasis","cat-oasis","lake","cat-lake","water-body","cat-lake","power-site","cat-sacred-site",'
        '"route-node","cat-route-node","ruins","cat-dungeon",'
        '"sacred-site","cat-sacred-site","site","cat-poi","cat-poi"]]'
    )


def _mini_map_tiered_layers_js(own_slug: str = '') -> str:
    """Build the tiered loc-overlay symbol layers for a mini-map (see _MINI_MAP_TIERS),
    plus hover-cursor and click-to-navigate handlers shared across all four tiers.

    Slugs come from each feature's `properties.slug` (set by
    _build_locations_geojson), not `feature.id` — MapLibre's GeoJSON source
    auto-generates its own internal numeric id unless `promoteId` is set,
    silently overriding the string id we set in the GeoJSON, so `.id` is
    unreliable for this. own_slug is excluded so clicking the current
    location's own marker doesn't just reload the same page.
    """
    icon_match = _mini_map_icon_match()
    js = ''
    layer_ids: list[str] = []
    for layer_id, cats, minzoom, fade_start, fade_end, label_font, label_size in _MINI_MAP_TIERS:
        cats_json = str(cats).replace("'", '"')
        opacity_expr = f'["interpolate",["linear"],["zoom"],{fade_start},0,{fade_end},0.9]'
        sz_expr = '["interpolate",["linear"],["zoom"],5,0.5,9,0.85]'
        layout = f'"icon-image":{icon_match},"icon-size":{sz_expr},"icon-allow-overlap":true,"icon-anchor":"center"'
        paint = f'"icon-opacity":{opacity_expr}'
        if label_font:
            font_json = str(label_font).replace("'", '"')
            layout += (
                f',"text-field":["case",["==",["get","mapLabel"],false],"",["get","label"]]'
                f',"text-font":{font_json},"text-size":{label_size}'
                f',"text-offset":[0,1],"text-anchor":"top","text-max-width":8'
                f',"text-allow-overlap":false,"text-optional":true'
            )
            paint += (
                f',"text-color":"#ffffff","text-halo-color":"rgba(10,8,5,0.95)"'
                f',"text-halo-width":1.5,"text-opacity":{opacity_expr}'
            )
        cat_filter = f'["all",["match",["get","category"],{cats_json},true,false],["!=",["get","mapMarker"],false]]'
        js += (
            f'map.addLayer({{id:"{layer_id}",type:"symbol",minzoom:{minzoom},source:"loc-overlay",'
            f'filter:{cat_filter},layout:{{{layout}}},paint:{{{paint}}}}});\n'
        )
        layer_ids.append(layer_id)

    ids_js = str(layer_ids).replace("'", '"')
    own_slug_json = json.dumps(own_slug)
    js += (
        f'{ids_js}.forEach(function(lyr){{\n'
        '  map.on("mouseenter",lyr,function(){map.getCanvas().style.cursor="pointer";});\n'
        '  map.on("mouseleave",lyr,function(){map.getCanvas().style.cursor="";});\n'
        '  map.on("click",lyr,function(e){\n'
        '    var slug=e.features[0].properties.slug||"";\n'
        f'    if(slug&&slug!=={own_slug_json})window.location.href="/locations/"+slug+".html";\n'
        '  });\n'
        '});\n'
    )
    return js


def render_mini_map(
    loc: LocationData,
    locations_geojson: Optional[dict] = None,
    routes_geojson: Optional[dict] = None,
    waystations_geojson: Optional[dict] = None,
    zoom: float = 6,
) -> str:
    """Render a MapLibre mini-map div for a single location.

    Uses the same custom icon sprites as the world home map, and the same
    zoom-tiered reveal system (_MINI_MAP_TIERS) for neighboring markers.
    Inlines GeoJSON data as JS variables; attribution control is suppressed.
    """
    if loc['lat'] is None or loc['lon'] is None:
        return '<div class="mini-map mini-map--no-coords"><p>No coordinates available.</p></div>\n'

    map_id = f'map-{escape(loc["slug"])}'
    lat = loc['lat']
    lon = loc['lon']
    effective_zoom = loc.get('map_zoom')
    if effective_zoom is None:
        effective_zoom = zoom
    effective_min_zoom = loc.get('map_min_zoom')
    if effective_min_zoom is None:
        effective_min_zoom = 5
    effective_max_zoom = loc.get('map_max_zoom')
    if effective_max_zoom is None:
        effective_max_zoom = 9
    drag_pan_js = 'true' if loc.get('map_pan', True) else 'false'
    own_marker_js = (
        '' if loc.get('map_marker') is False
        else f"new maplibregl.Marker({{color: '#7a1f1f'}}).setLngLat([{lon}, {lat}]).addTo(map);"
    )

    sources_js = ''
    layers_js = ''

    if routes_geojson:
        sources_js += f'map.addSource("routes-overlay",{{type:"geojson",data:{json.dumps(routes_geojson)}}});\n'
        layers_js += (
            'map.addLayer({id:"routes-overlay",type:"line",source:"routes-overlay",minzoom:4,'
            'paint:{"line-color":"#1a1208","line-width":4,"line-opacity":0.85}});\n'
        )

    if waystations_geojson or locations_geojson:
        # Register the sprite atlas once; both waystations and location layers use it.
        layers_js += icon_registration_js()

    if waystations_geojson:
        sources_js += f'map.addSource("waystations-overlay",{{type:"geojson",data:{json.dumps(waystations_geojson)}}});\n'
        layers_js += (
            'map.addLayer({id:"waystations-overlay",type:"symbol",'
            'source:"waystations-overlay",minzoom:5,'
            'layout:{"icon-image":"cat-route-node","icon-size":0.7,'
            '"text-field":["case",["!=",["get","osm_name"],null],["get","osm_name"],""],'
            '"text-size":9,"text-offset":[0,0.8],"text-anchor":"top","text-optional":true},'
            'paint:{"icon-opacity":0.5,"text-color":"#cccccc",'
            '"text-halo-color":"rgba(10,8,5,0.95)","text-halo-width":1}});\n'
        )

    if locations_geojson:
        sources_js += f'map.addSource("loc-overlay",{{type:"geojson",data:{json.dumps(locations_geojson)}}});\n'
        layers_js += _mini_map_tiered_layers_js(own_slug=loc['slug'])

    return f"""<div class="mini-map" id="{map_id}"></div>
{MAP_ATTRIBUTION_HTML}
<script>
(function() {{
  var map = new maplibregl.Map({{
    container: '{map_id}',
    style: '{MAPTILER_STYLE_URL}',
    center: [{lon}, {lat}],
    zoom: {effective_zoom},
    minZoom: {effective_min_zoom},
    maxZoom: {effective_max_zoom},
    dragPan: {drag_pan_js},
    scrollZoom: true,
    boxZoom: false,
    dragRotate: false,
    keyboard: false,
    doubleClickZoom: true,
    touchZoomRotate: false,
    attributionControl: false
  }});
  map.on('load', function() {{
    {sources_js}
    {layers_js}
    {own_marker_js}
  }});
}})();
</script>
"""


# ---------------------------------------------------------------------------
# Cross-reference stub
# ---------------------------------------------------------------------------

def render_xref_stub(label: str = "Related Locations") -> str:
    """Stub cross-reference panel — populated by future cross-link pass."""
    return (
        f'<div class="xref-stub">'
        f'<span class="xref-stub__label">{escape(label)}</span>'
        f'<span class="xref-stub__note">cross-links pending</span>'
        f'</div>\n'
    )
