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


# ---------------------------------------------------------------------------
# Danger / tier pips
# ---------------------------------------------------------------------------

_DANGER_BY_TYPE: dict[str, int] = {
    "city": 1,
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
# Leaflet tile configuration — single source of truth for both mini-maps
# and the full world map in generate_locations_html.py
#
# Tile provider is switchable at request time via ?tiles= URL param.
# Default: physical. Options: physical | relief | satellite
# All three are ESRI — no API key, free for non-commercial use.
# Interim setup — replaced by MapTiler vector tiles in Phase B5.
# ---------------------------------------------------------------------------

ESRI_ATTR = (
    "&copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, "
    "Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community"
)

# JS snippet embedded in every map — reads ?tiles= param and picks tile URL.
# Defined once here; interpolated into both mini-map and world-map templates.
TILE_SWITCHER_JS = """var _tiles = {
    physical:  'https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}',
    relief:    'https://server.arcgisonline.com/ArcGIS/rest/services/World_Shaded_Relief/MapServer/tile/{z}/{y}/{x}',
    satellite: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'
  };
  var _tileKey = new URLSearchParams(window.location.search).get('tiles');
  var _tileUrl = _tiles[_tileKey] || _tiles.physical;"""

TILE_LAYER_JS = f"L.tileLayer(_tileUrl, {{maxZoom: 18, attribution: '{ESRI_ATTR}'}}).addTo(map);"

# Combined attribution string for static map credit divs
MAP_ATTRIBUTION_HTML = (
    f'<div class="map-attribution">'
    f'Map &copy; <a href="https://www.esri.com/" target="_blank" rel="noopener">Esri</a>'
    f'</div>'
)


def render_mini_map(
    loc: LocationData,
    locations_geojson: Optional[dict] = None,
    routes_geojson: Optional[dict] = None,
    zoom: int = 6,
) -> str:
    """Render a Leaflet mini-map div for a single location.

    Inlines GeoJSON data as JavaScript variables to avoid cross-origin issues.
    Attribution control is suppressed on the small fixed map; a static credit
    line is appended below instead.
    """
    if loc['lat'] is None or loc['lon'] is None:
        return '<div class="mini-map mini-map--no-coords"><p>No coordinates available.</p></div>\n'

    map_id = f'map-{escape(loc["slug"])}'
    lat = loc['lat']
    lon = loc['lon']

    layers_js = ''
    if locations_geojson:
        layers_js += f'var _locationsGeoJSON = {json.dumps(locations_geojson)};\n'
    if routes_geojson:
        layers_js += f'var _routesGeoJSON = {json.dumps(routes_geojson)};\n'

    geojson_layers = ''
    if locations_geojson:
        geojson_layers += (
            'L.geoJSON(_locationsGeoJSON, {'
            'pointToLayer: function(f,ll){return L.circleMarker(ll,{radius:5,color:"#b8892a",weight:2,fillOpacity:0.7});}'
            '}).addTo(map);\n'
        )
    if routes_geojson:
        geojson_layers += (
            'L.geoJSON(_routesGeoJSON, {style:{color:"#b8892a",weight:2,opacity:0.6}}).addTo(map);\n'
        )

    return f"""<div class="mini-map" id="{map_id}"></div>
{MAP_ATTRIBUTION_HTML}
<script>
(function() {{
  {layers_js}
  var map = L.map('{map_id}', {{
    center: [{lat}, {lon}],
    zoom: {zoom},
    zoomControl: false,
    attributionControl: false,
    dragging: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    touchZoom: false
  }});
  {TILE_SWITCHER_JS}
  {TILE_LAYER_JS}
  {geojson_layers}
  L.circleMarker([{lat}, {lon}], {{radius: 8, color: '#7a1f1f', weight: 3, fillColor: '#f5edd8', fillOpacity: 1}}).addTo(map);
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
