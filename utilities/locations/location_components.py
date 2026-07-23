"""
Location HTML component renderers.

Each function takes structured data and returns an HTML fragment string.
Used by the main generator to assemble location detail pages.
"""

import json
from html import escape
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
# The base map is now a self-hosted static raster tile pyramid (docs/tiles/),
# generated from the georeferenced Wonderdraft art -- no external tile
# service, no API key. See utilities/world/GEOREFERENCING.md and
# https://github.com/mofro/tarim-shaiel-campaign-frame/issues/275
#
# `glyphs` is intentionally omitted: MapLibre falls back to local/system
# fonts for text-field rendering when it's unset (confirmed via the style
# spec -- omitting it doesn't error or hide labels, it just doesn't use the
# custom PBF font atlas a hosted style would normally provide).
# ---------------------------------------------------------------------------

# Bounds computed from the QGIS thin-plate-spline georeferencing pass
# (2026-07-22, 12 GCPs) -- [west, south, east, north].
MAP_BOUNDS = [47.9030620, 25.3876570, 123.0647401, 51.4063843]

MAPLIBRE_LOCAL_STYLE = {
    'version': 8,
    'sources': {
        'tarim-shaiel-raster': {
            'type': 'raster',
            'tiles': ['/tiles/{z}/{x}/{y}.png'],
            'tileSize': 256,
            'bounds': MAP_BOUNDS,
            'minzoom': 5,
            'maxzoom': 8,
            # gdal2tiles.py outputs TMS scheme (Y from south) by default,
            # not XYZ (Y from north) -- without this, tiles 404 against the
            # wrong Y coordinate. See HeroHeaven-1yu.
            'scheme': 'tms',
        },
    },
    'layers': [
        {
            'id': 'tarim-shaiel-base',
            'type': 'raster',
            'source': 'tarim-shaiel-raster',
        },
    ],
}
MAPLIBRE_STYLE_JSON = json.dumps(MAPLIBRE_LOCAL_STYLE)

# Attribution shown below non-interactive mini-maps. No external tile
# provider to credit anymore -- this is the campaign's own art.
MAP_ATTRIBUTION_HTML = (
    '<div class="map-attribution">'
    'Map art &copy; Tarim-Shaiel'
    '</div>'
)


# Mirrors the tier structure in generate_locations_html.py::_locations_layers_js
# (same category groupings + zoom thresholds) so mini-maps and the world map
# reveal locations the same way as you zoom. Duplicated rather than imported —
# generate_locations_html.py imports FROM this module, so importing back would
# create a circular dependency.
_MINI_MAP_TIERS = [
    # Thresholds shifted down by 1 from the original 3/5/6/7 minzoom scheme
    # to fit the new mini-map range (map_max_zoom now 7, was 8) -- otherwise
    # "detail" (fade 7.5->8) would never reach full opacity within the new
    # max zoom. Kept in sync with generate_locations_html.py's tiers.
    # layer_id            categories                                    mz  fs   fe   label_font                                     size
    ('mm-locations-major',     ['city', 'landmark', 'fortress'],             2, 2.5, 3,  ['Roboto Serif Regular', 'Noto Sans Bold'],   12),
    ('mm-locations-secondary', ['sacred-site', 'oasis', 'caravanserai'],     4, 4.5, 5,  ['Roboto Serif Regular', 'Noto Sans Italic'], 11),
    ('mm-locations-routes',    ['route-node', 'chokepoint', 'mountain-pass'],5, 5.5, 6,  None,                                       0),
    ('mm-locations-detail',    ['ruins', 'poi', 'power-site', 'site'],       6, 6.5, 7,  None,                                       0),
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
        '"city","cat-city","caravanserai","cat-route-node",'
        '"chokepoint","cat-fortress","mountain-pass","cat-landmark",'
        '"oasis","cat-oasis","power-site","cat-sacred-site",'
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
        layout = f'"icon-image":{icon_match},"icon-size":1,"icon-allow-overlap":true,"icon-anchor":"center"'
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
        effective_min_zoom = 6
    effective_max_zoom = loc.get('map_max_zoom')
    if effective_max_zoom is None:
        effective_max_zoom = 7
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
            'paint:{"line-color":"#b8892a","line-width":2,"line-opacity":0.6}});\n'
        )

    if locations_geojson:
        sources_js += f'map.addSource("loc-overlay",{{type:"geojson",data:{json.dumps(locations_geojson)}}});\n'
        layers_js += icon_registration_js()
        layers_js += _mini_map_tiered_layers_js(own_slug=loc['slug'])

    return f"""<div class="mini-map" id="{map_id}" style="position:relative;">
  <div id="{map_id}-zoom-debug" style="position:absolute;top:8px;left:8px;z-index:5;background:rgba(10,8,5,0.85);color:#fff;font:12px monospace;padding:2px 6px;border-radius:3px;pointer-events:none;">zoom: —</div>
</div>
{MAP_ATTRIBUTION_HTML}
<script>
(function() {{
  var map = new maplibregl.Map({{
    container: '{map_id}',
    style: {MAPLIBRE_STYLE_JSON},
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
  // TEMP DEBUG — zoom-level readout, remove when done testing
  var zoomDebugEl = document.getElementById('{map_id}-zoom-debug');
  function updateZoomDebug() {{ zoomDebugEl.textContent = 'zoom: ' + map.getZoom().toFixed(2); }}
  map.on('zoom', updateZoomDebug);
  map.on('load', updateZoomDebug);
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
