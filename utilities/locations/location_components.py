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
# Style JSON lives at /assets/map-style.json (copied from utilities/assets/
# to docs/assets/ at build time). MapTiler API key is baked into the style.
# ---------------------------------------------------------------------------

# Attribution shown below non-interactive mini-maps (world map uses built-in
# MapLibre attribution control which reads from the style JSON).
MAP_ATTRIBUTION_HTML = (
    '<div class="map-attribution">'
    'Map &copy; <a href="https://www.maptiler.com/" target="_blank" rel="noopener">MapTiler</a> / '
    '<a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">OSM</a>'
    '</div>'
)


def render_mini_map(
    loc: LocationData,
    locations_geojson: Optional[dict] = None,
    routes_geojson: Optional[dict] = None,
    zoom: int = 6,
) -> str:
    """Render a MapLibre mini-map div for a single location.

    Uses the same custom icon sprites and symbol layers as the world home map.
    Inlines GeoJSON data as JS variables; attribution control is suppressed.
    """
    if loc['lat'] is None or loc['lon'] is None:
        return '<div class="mini-map mini-map--no-coords"><p>No coordinates available.</p></div>\n'

    map_id = f'map-{escape(loc["slug"])}'
    lat = loc['lat']
    lon = loc['lon']

    icon_match = (
        '"icon-image":["match",["get","category"],'
        '"city","cat-city","caravanserai","cat-route-node",'
        '"chokepoint","cat-fortress","mountain-pass","cat-landmark",'
        '"oasis","cat-oasis","power-site","cat-sacred-site",'
        '"route-node","cat-route-node","ruins","cat-dungeon",'
        '"sacred-site","cat-sacred-site","site","cat-poi","cat-poi"],'
        '"icon-size":1,"icon-allow-overlap":true,"icon-anchor":"center"'
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
        # All locations — icons only, always visible at mini-map zoom
        layers_js += (
            f'map.addLayer({{id:"loc-overlay",type:"symbol",source:"loc-overlay",'
            f'layout:{{{icon_match}}},'
            f'paint:{{"icon-opacity":0.9}}}});\n'
        )

    return f"""<div class="mini-map" id="{map_id}"></div>
{MAP_ATTRIBUTION_HTML}
<script>
(function() {{
  var map = new maplibregl.Map({{
    container: '{map_id}',
    style: 'https://api.maptiler.com/maps/019e13d9-26c8-7cd9-bf8d-64d83f66624e/style.json?key=uZtsACZHTZGwWfZ3HGai',
    center: [{lon}, {lat}],
    zoom: {zoom},
    maxZoom: 11,
    interactive: false,
    attributionControl: false
  }});
  map.on('load', function() {{
    {sources_js}
    {layers_js}
    new maplibregl.Marker({{color: '#7a1f1f'}}).setLngLat([{lon}, {lat}]).addTo(map);
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
