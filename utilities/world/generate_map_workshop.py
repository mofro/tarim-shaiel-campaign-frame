#!/usr/bin/env python3
"""
Generate map-workshop.html — local GM-only visual workflow entry point.

Opens directly in a browser (no server needed). Gitignored — contains
the MapTiler API key and all GM location data. Regenerate whenever
locations or routes change.

Usage:
    python utilities/world/generate_map_workshop.py
    open map-workshop.html
"""

import json
import math
import os
import sys
import urllib.parse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent

sys.path.insert(0, str(SCRIPT_DIR.parent))

from locations.categories import CATEGORIES
from locations.location_parser import load_all_locations
from locations.map_icons import icon_registration_js
from locations.location_components import MAPTILER_STYLE_URL, MAPTILER_KEY, MAPTILER_STYLE_ID
from shared import journeys, map_style, route_visibility, travel_time

LOCATIONS_DIR = VAULT_ROOT / "world" / "locations"
ROUTES_PATH   = VAULT_ROOT / "world" / "data" / "tarim-shaiel-routes.geojson"
REGIONS_PATH  = VAULT_ROOT / "world" / "data" / "tarim-shaiel-regions.geojson"
JOURNEYS_PATH = VAULT_ROOT / "world" / "data" / "tarim-shaiel-journeys.geojson"
OUTPUT_PATH   = VAULT_ROOT / "map-workshop.html"
PLAYER_PATH   = VAULT_ROOT / "player-map.html"


# ---------------------------------------------------------------------------
# Geometry helpers (inlined from generate_routes.py)
# ---------------------------------------------------------------------------

def haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def path_length_km(coords: list) -> float:
    total = 0.0
    for i in range(len(coords) - 1):
        total += haversine_km(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
    return total


# ---------------------------------------------------------------------------
# Data builders
# ---------------------------------------------------------------------------

def _build_locations_geojson(locations: list) -> dict:
    features = []
    for loc in locations:
        if loc["lat"] is None or loc["lon"] is None:
            continue
        props = {
            "kind":        "location",
            "category":    loc["location_type"],
            "label":       loc["fantasy_name"] or loc["title"],
            "title":       loc["title"],
            "description": loc["description"],
            "fantasyName": loc["fantasy_name"],
            "visibility":  loc["visibility"],
            "mapLabel":    loc["map_label"],
            "mapMarker":   loc["map_marker"],
            "slug":        loc["slug"],
            "_slug":       loc["slug"],
        }
        popup_desc = map_style.popup_description(loc["description"])
        if popup_desc:
            props["popupDesc"] = popup_desc
        features.append({
            "type": "Feature",
            "id": f'location_{loc["slug"]}',
            "properties": props,
            "geometry": {
                "type": "Point",
                "coordinates": [loc["lon"], loc["lat"]],
            },
        })
    return {"type": "FeatureCollection", "features": features}


def _player_locations_geojson(loc_geojson: dict) -> dict:
    """Player copy of the locations GeoJSON: public features only, GM view stripped.

    The raw `description` is dropped (it can hold session notes) and popupDesc is
    recomputed with the player-safe filter, so what players see is exactly what
    ships in the page source.
    """
    features = []
    for f in loc_geojson["features"]:
        props = f["properties"]
        if props.get("visibility", "public") == "gm_secrets":
            continue
        pub = {k: v for k, v in props.items() if k not in ("description", "popupDesc")}
        popup_desc = map_style.popup_description(props.get("description"), player_safe=True)
        if popup_desc:
            pub["popupDesc"] = popup_desc
        features.append({**f, "properties": pub})
    return {**loc_geojson, "features": features}


def annotate_routes(routes_geojson: dict, all_locations_gj: dict | None) -> dict:
    """Workshop copy of the routes with build-time `_playerVisible` / `_endsPublic`.

    `_playerVisible` is the route_visibility rule (own visibility public AND both
    ends public); `_endsPublic` says whether the ends alone would allow it. Both
    are computed here, never persisted to the routes file.
    """
    points = route_visibility._location_points(all_locations_gj or {})
    feats = []
    for f in routes_geojson.get("features", []):
        a, b = route_visibility.route_endpoints(f, points)
        ends_public = bool(a and b and a[2] != route_visibility.GM_ONLY
                           and b[2] != route_visibility.GM_ONLY)
        own_public = f.get("properties", {}).get("visibility") == route_visibility.PUBLIC
        props = {**f.get("properties", {}),
                 "_endsPublic": ends_public,
                 "_playerVisible": ends_public and own_public}
        feats.append({**f, "properties": props})
    return {**routes_geojson, "features": feats}


def _build_route_index(routes_geojson: dict) -> list:
    """Rows for the route index. Expects features from `annotate_routes`."""
    results = []
    for feat in routes_geojson.get("features", []):
        fid = feat.get("id", "")
        props = feat.get("properties", {})
        coords = feat.get("geometry", {}).get("coordinates", [])
        label = props.get("route_name") or props.get("label") or props.get("title") or fid
        kind = "spur" if fid.startswith("route_spur_") else "main"
        is_approx = len(coords) <= 2
        dist_km = travel_time.line_length_km(coords)
        mode = travel_time.normalize_mode(props.get("mode"))
        hours = travel_time.segment_hours(
            dist_km, mode, "straight" if is_approx else "road")
        results.append({
            "id": fid, "label": label, "kind": kind,
            "dist_km": round(dist_km, 0), "is_approx": is_approx,
            "mode": mode, "hours": hours,
            "time": travel_time.format_duration(hours, approx=is_approx),
            "visibility": props.get("visibility", route_visibility.GM_ONLY),
            "player_visible": bool(props.get("_playerVisible")),
        })
    results.sort(key=lambda r: (r["kind"] != "main", r["id"]))
    return results


def _route_index_html(route_index: list) -> str:
    main_routes = [r for r in route_index if r["kind"] == "main"]
    spurs = [r for r in route_index if r["kind"] == "spur"]

    def row(r: dict) -> str:
        p = "~" if r["is_approx"] else ""
        d = f'{p}{int(r["dist_km"])} km'
        mode = travel_time.SPEEDS[r["mode"]]["label"]
        if r["player_visible"]:
            vis = '<span class="ri-vis ri-vis-pub" title="Players see this route">players</span>'
        elif r["visibility"] == route_visibility.PUBLIC:
            vis = '<span class="ri-vis ri-vis-held" title="Route is public but an end location is hidden">held</span>'
        else:
            vis = '<span class="ri-vis ri-vis-gm" title="GM only">GM</span>'
        return (
            f'<tr class="ri-row" data-id="{r["id"]}" style="cursor:pointer">'
            f'<td class="ri-check"><input type="checkbox" class="ri-cb" data-id="{r["id"]}"></td>'
            f'<td class="ri-id">{r["id"]}</td>'
            f'<td>{r["label"]}</td>'
            f'<td>{d}</td>'
            f'<td>{r["time"]} <span class="ri-mode">{mode}</span></td>'
            f'<td>{vis}</td>'
            f'</tr>'
        )

    def section(title: str, rows: list) -> str:
        if not rows:
            return ""
        thead = ('<thead><tr><th class="ri-check"></th><th>ID</th><th>Label</th>'
                 '<th>Distance</th><th>Travel</th><th>Seen by</th></tr></thead>')
        tbody = "<tbody>" + "".join(row(r) for r in rows) + "</tbody>"
        return f"<h3>{title}</h3><table>{thead}{tbody}</table>"

    header = (
        '<div class="ri-header">'
        '<label class="ri-select-all-label">'
        '<input type="checkbox" id="ri-select-all"> Select All'
        '</label>'
        '<button id="ri-delete-btn" hidden>🗑 Delete Selected (0)</button>'
        '</div>'
    )
    note = ('<p class="ri-note">~ = straight-line estimate (2-point segment, not road-routed). '
            'Travel uses each route\'s mode (default foot). '
            '"held" = route is public but an end location is still hidden.</p>')
    return (
        header
        + section("Main Routes", main_routes)
        + section("Spurs", spurs)
        + note
    )


# ---------------------------------------------------------------------------
# HTML / JS builders
# ---------------------------------------------------------------------------

_CSS = """\
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; overflow: hidden; font-family: 'Georgia', serif;
  background: #0a0805; color: #e8dcc4; }
#app { display: flex; height: 100vh; position: relative; }
#sidebar { min-width: 340px; display: flex; flex-direction: column;
  background: #120f08; border-right: 1px solid rgba(184,146,44,0.3); overflow: hidden; }
#sidebar-header { padding: 12px 14px 0; border-bottom: 1px solid rgba(184,146,44,0.2);
  flex-shrink: 0; }
#app-title { font-size: 13px; letter-spacing: 0.12em; text-transform: uppercase;
  color: #b8922c; margin-bottom: 6px; }
#tab-bar { display: flex; gap: 2px; }
.tab-btn { flex: 1; padding: 7px 2px; font-size: 10px; letter-spacing: 0.05em;
  text-transform: uppercase; background: #1a1410; border: 1px solid rgba(184,146,44,0.2);
  border-bottom: none; color: #8a7a60; cursor: pointer; border-radius: 3px 3px 0 0;
  transition: background 0.15s; }
.edit-badge { display: inline-block; background: #6a9a2c; color: #fff; font-size: 9px;
  border-radius: 8px; padding: 0 4px; margin-left: 3px; line-height: 14px; vertical-align: middle; }
.tab-btn:hover { background: #221c12; color: #c8a84a; }
.tab-btn.active { background: #0a0805; color: #e8dcc4; border-color: rgba(184,146,44,0.4);
  border-bottom-color: #0a0805; font-weight: bold; }
.panel { display: none; flex-direction: column; flex: 1; overflow-y: auto;
  padding: 14px; gap: 12px; }
.panel.active { display: flex; }
.field-group { display: flex; flex-direction: column; gap: 4px; }
.field-group label { font-size: 11px; text-transform: uppercase; letter-spacing: 0.07em;
  color: #9a8a6a; }
.field-group input[type="text"], .field-group select, .field-group textarea {
  background: #1a1410; border: 1px solid rgba(184,146,44,0.3); color: #e8dcc4;
  padding: 6px 8px; font-size: 13px; border-radius: 2px; font-family: inherit; }
.field-group input[type="text"]:focus, .field-group select:focus, .field-group textarea:focus {
  outline: none; border-color: rgba(184,146,44,0.7); }
.field-group select option { background: #1a1410; }
.field-group textarea { resize: vertical; min-height: 56px; }
.coord-row { display: flex; gap: 6px; align-items: center; font-size: 12px; }
.coord-row span { color: #9a8a6a; font-size: 11px; }
.coord-row input { flex: 1; }
.radio-row { display: flex; gap: 14px; font-size: 13px; }
.radio-row label { display: flex; align-items: center; gap: 5px; cursor: pointer; }
.radio-row input[type="radio"] { accent-color: #b8922c; }
.btn { padding: 8px 14px; background: #2a1e08; border: 1px solid rgba(184,146,44,0.5);
  color: #e8dcc4; font-size: 12px; cursor: pointer; border-radius: 2px;
  letter-spacing: 0.05em; transition: background 0.15s; }
.btn:hover:not(:disabled) { background: #3a2a10; border-color: #b8922c; }
.btn:disabled { opacity: 0.4; cursor: default; }
.btn-sm { padding: 5px 10px; font-size: 11px; }
.btn-danger { border-color: rgba(180, 60, 60, 0.5); }
.btn-danger:hover:not(:disabled) { background: #3a1010; border-color: #b83c3c; }
.btn-row { display: flex; gap: 6px; }
.command-block { background: #0d0a06; border: 1px solid rgba(184,146,44,0.3);
  border-radius: 2px; overflow: hidden; }
.command-block pre { padding: 10px 12px; font-size: 11px; font-family: monospace;
  white-space: pre-wrap; word-break: break-all; color: #c8b890; line-height: 1.5; }
.command-block .btn { border-radius: 0; border: none; border-top: 1px solid rgba(184,146,44,0.2);
  width: 100%; text-align: center; }
.hint { font-size: 11px; color: #7a6a50; line-height: 1.5; }
.hint code { font-family: monospace; color: #9a8a60; background: rgba(255,255,255,0.04);
  padding: 1px 4px; border-radius: 2px; }
.hidden { display: none !important; }
/* Route queue */
#route-queue-list { list-style: none; display: flex; flex-direction: column; gap: 4px; }
.queue-item { background: #1a1410; border: 1px solid rgba(184,146,44,0.2);
  border-radius: 2px; padding: 7px 10px; font-size: 12px; }
.queue-item .qi-num { color: #b8922c; font-weight: bold; margin-right: 6px; }
.queue-item .qi-label { color: #e8dcc4; }
.queue-item .qi-dist { color: #7a6a50; font-size: 11px; margin-top: 2px; }
.queue-empty { color: #5a4a30; font-size: 12px; font-style: italic; }
/* Panel widths */
#panel-plan-route, #panel-add-point, #panel-edit-coords { max-width: 340px; }
/* Route index */
.panel#panel-route-index { gap: 8px; }
#panel-route-index h3 { font-size: 12px; text-transform: uppercase;
  letter-spacing: 0.1em; color: #b8922c; margin-top: 6px; }
#panel-route-index table { width: 100%; border-collapse: collapse; font-size: 11px; }
#panel-route-index th { color: #9a8a6a; text-align: left; padding: 4px 6px;
  border-bottom: 1px solid rgba(184,146,44,0.2); }
#panel-route-index td { padding: 4px 6px; border-bottom: 1px solid rgba(255,255,255,0.04); }
#panel-route-index .ri-id { font-family: monospace; color: #7a6a50; font-size: 10px; }
.ri-note { font-size: 10px; color: #5a4a30; margin-top: 4px; }
.ri-row:hover td { background: rgba(184,146,44,0.07); }
.ri-row.active td { background: rgba(184,146,44,0.14); }
/* Route section separator */
.route-or { text-align: center; color: #5a4a30; font-size: 11px; margin: 4px 0; }
/* Route index delete controls */
.ri-header { display:flex; align-items:center; gap:8px; padding:4px 0 8px; }
.ri-select-all-label { font-size:11px; color:#9a8a6a; display:flex; align-items:center; gap:5px; cursor:pointer; }
.ri-select-all-label input { accent-color:#b8922c; }
#ri-delete-btn { padding:4px 10px; font-size:11px; background:#2a0e08;
  border:1px solid rgba(180,60,60,0.5); color:#e8a090; cursor:pointer; border-radius:2px; }
#ri-delete-btn:hover { background:#3a1010; border-color:#b83c3c; }
.ri-check { width:28px; text-align:center; }
.ri-check input[type=checkbox] { accent-color:#b8922c; cursor:pointer; }
.ri-mode { color:#7a6a50; font-size:10px; }
.ri-vis { font-size:10px; padding:1px 6px; border-radius:8px; border:1px solid transparent; }
.ri-vis-pub { color:#9bc47a; border-color:rgba(155,196,122,0.4); }
.ri-vis-held { color:#d9a441; border-color:rgba(217,164,65,0.4); }
.ri-vis-gm { color:#8a7a5a; border-color:rgba(138,122,90,0.35); }
/* Route panel overlay (map-click selection) */
#route-panel { position:absolute; top:10px; right:10px; z-index:10;
  background:#1a1208; color:#f0e6c8; padding:10px 14px; border-radius:6px;
  border:1px solid #b8922c; min-width:180px; font-size:12px;
  box-shadow:0 2px 12px rgba(0,0,0,0.6); }
#route-panel-label { font-weight:bold; margin-bottom:8px; word-break:break-word; }
#route-panel .rp-row { display:flex; align-items:center; gap:8px; margin-bottom:6px; }
#route-panel .rp-row label { font-size:11px; color:#8a7a5a; min-width:52px; }
#route-panel .rp-row select { flex:1; background:#1a1408; color:#e8dcc4;
  border:1px solid rgba(184,146,44,0.35); padding:3px 4px; font-size:11px; border-radius:3px; }
#route-panel-time { font-size:11px; color:#c8b98a; margin-bottom:4px; }
#route-panel-seen { font-size:11px; margin-bottom:8px; color:#8a7a5a; }
#route-panel-seen.rp-yes { color:#9bc47a; }
#route-panel-seen.rp-held { color:#d9a441; }
#route-panel-regenerate { background:#4a3418; color:#e8dcc4; border:1px solid #b8922c;
  padding:4px 10px; border-radius:4px; cursor:pointer; font-size:11px; }
#route-panel-regenerate:hover { background:#5a4020; }
#route-panel-regenerate:disabled { opacity:0.5; cursor:default; }
#route-panel-delete { background:#c0392b; color:#fff; border:none;
  margin-left:6px; padding:4px 10px; border-radius:4px; cursor:pointer; font-size:11px; }
#route-panel-delete:hover { background:#e74c3c; }
#route-panel-close { margin-left:6px; background:none; color:#b8922c;
  border:1px solid rgba(184,146,44,0.5); padding:3px 7px; border-radius:4px;
  cursor:pointer; font-size:11px; }
#route-panel-close:hover { border-color:#b8922c; color:#e8dcc4; }
/* Map */
#map { flex: 1; }
.maplibregl-map { font: inherit; }
/* Edit Coords panel */
.list-heading { font-size: 11px; text-transform: uppercase; letter-spacing: 0.07em;
  color: #9a8a6a; margin-bottom: 6px; margin-top: 8px; }
.edit-toggle { width: 100%; text-align: center; transition: background 0.15s, border-color 0.15s; }
/* Devserver banner */
#ds-banner { display:flex; align-items:center; gap:8px; padding:5px 14px;
  background:#3a1a00; border-bottom:1px solid rgba(220,100,30,0.5);
  font-size:11px; color:#e8a060; flex-shrink:0; }
#ds-banner[hidden] { display:none; }
#ds-banner code { font-family:monospace; background:rgba(255,255,255,0.08);
  padding:1px 5px; border-radius:2px; color:#f0c090; }
#ds-banner-close { margin-left:auto; background:none; border:none; color:#e8a060;
  cursor:pointer; font-size:14px; line-height:1; padding:0 2px; }
/* Subheader toolbar */
#ws-subheader { display:flex; align-items:center; gap:8px; padding:5px 0 6px;
  border-bottom:1px solid rgba(184,146,44,0.15); position:relative; margin-bottom:6px; }
#layers-btn { background:none; border:1px solid rgba(184,146,44,0.4); color:#c8a84a;
  padding:3px 9px; border-radius:3px; font-size:11px; cursor:pointer;
  letter-spacing:0.05em; text-transform:uppercase; font-family:inherit; }
#layers-btn:hover { border-color:#b8922c; color:#e8dcc4; }
#layers-btn.open { background:rgba(184,146,44,0.1); border-color:#b8922c; }
#layers-dropdown { position:absolute; top:calc(100% + 1px); left:0; z-index:20;
  background:rgba(22,14,5,0.97); border:1px solid rgba(184,146,44,0.4);
  border-radius:0 5px 5px 5px; padding:10px 14px;
  min-width:280px; box-shadow:2px 6px 18px rgba(0,0,0,0.7);
  backdrop-filter:blur(4px); color:#f0e6c8; }
#layers-dropdown label { display:flex; align-items:center; gap:6px; cursor:pointer;
  white-space:nowrap; color:#c8a84a; text-transform:uppercase; letter-spacing:0.06em; }
#layers-dropdown label + label { margin-top:5px; }
#layers-dropdown hr { border:none; border-top:1px solid rgba(184,146,44,0.25); margin:6px 0 5px; }
#topo-toggle,#sat-toggle { accent-color:#b8922c; cursor:pointer; }
#topo-opacity,#sat-opacity { accent-color:#b8922c; width:72px; cursor:pointer; }
#ws-zoom { margin-left:auto; color:#8a7a5a; font-size:12px; letter-spacing:0.06em; }
#ws-zoom-val { color:#c8a84a; font-weight:bold; }
#ws-edit-dot { font-size:11px; color:#a8d840; letter-spacing:0.04em; white-space:nowrap; }
.it-heading { font-size:10px; text-transform:uppercase; letter-spacing:0.07em; color:#8a7a5a; margin-bottom:3px; }
.it-grid { display:grid; grid-template-columns:1fr 1fr; gap:2px 10px; }
.it-grid label { display:flex; align-items:center; gap:5px; cursor:pointer; color:#c8b890;
  font-size:10px; text-transform:none; letter-spacing:0; white-space:nowrap; margin-top:0; }
.it-grid input[type=checkbox] { accent-color:#b8922c; cursor:pointer; }
.overlay-err { display:inline-flex; align-items:center; background:#7a1f00; color:#ffcc88;
  font-size:9px; padding:1px 4px; border-radius:3px; cursor:help; margin-left:2px; vertical-align:middle; }
.edit-toggle.active { background: #1a2a0a; border-color: #6a9a2c; color: #a8d840; }
.edit-toggle.active:hover { background: #263d12; border-color: #8aba40; }
#unsaved-list { list-style: none; display: flex; flex-direction: column; gap: 3px;
  max-height: 140px; overflow-y: auto; }
.unsaved-item { font-size: 11px; padding: 5px 8px; background: #1a1410;
  border: 1px solid rgba(184,146,44,0.15); border-radius: 2px; }
.ui-slug { font-family: monospace; color: #e8dcc4; }
.ui-coords { color: #7a6a50; margin-left: 6px; }
.rebuild-section { margin-top: 8px; }
#api-status { min-height: 16px; color: #9a8a6a; }
#api-status.ok { color: #6a9a2c; }
#api-status.err { color: #b83c3c; }
/* Reveal tab */
#panel-reveal { max-width: 340px; }
#rv-staged, #rv-hidden, #rv-confirm-list { list-style: none; display: flex;
  flex-direction: column; gap: 4px; }
#rv-hidden { max-height: 320px; overflow-y: auto; }
.rv-item { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.rv-main { flex: 1; min-width: 0; }
.rv-x, .rv-name { background: none; border: none; cursor: pointer; font-family: inherit; }
.rv-x { color: #9a8a6a; font-size: 12px; padding: 0 2px; }
.rv-x:hover { color: #e8dcc4; }
.rv-name { color: #e8dcc4; font-size: 12px; padding: 0; text-align: left; }
.rv-name:hover { color: #f5d060; }
.rv-err { color: #b83c3c; font-size: 11px; margin-top: 2px; }
#rv-confirm { border: 1px solid rgba(184,146,44,0.5); background: #1a1410;
  border-radius: 2px; padding: 8px 10px; }
#rv-confirm-list { font-size: 12px; color: #e8dcc4; max-height: 120px; overflow-y: auto;
  margin: 6px 0; padding-left: 14px; list-style: disc; }
#rv-status { min-height: 16px; color: #9a8a6a; }
#rv-status.ok { color: #6a9a2c; }
#rv-status.err { color: #b83c3c; }
.drag-edit-marker { width: 22px; height: 22px; background: #f5d060;
  border: 2.5px solid #2a1e08; border-radius: 50%; cursor: grab;
  box-shadow: 0 2px 10px rgba(0,0,0,0.6); }
.drag-edit-marker:active { cursor: grabbing; }
/* World link in header */
#app-title-link { font-size: 10px; text-transform: none; letter-spacing: 0.03em;
  color: #7a6a50; text-decoration: none; float: right; margin-top: 2px; }
#app-title-link:hover { color: #b8922c; }
/* Search row */
#ws-search-row { position: relative; padding: 5px 14px 6px; border-bottom: 1px solid rgba(184,146,44,0.1);
  flex-shrink: 0; }
#ws-search-wrap { position: relative; }
#ws-search-icon { position: absolute; left: 8px; top: 50%; transform: translateY(-50%);
  color: #5a4a30; font-size: 12px; pointer-events: none; line-height: 1; }
#ws-search { width: 100%; background: #1a1410; border: 1px solid rgba(184,146,44,0.25);
  color: #e8dcc4; padding: 5px 8px 5px 24px; font-size: 12px; border-radius: 2px;
  font-family: inherit; outline: none; }
#ws-search:focus { border-color: rgba(184,146,44,0.7); }
#ws-search-drop { position: absolute; top: 100%; left: 0; right: 0;
  background: rgba(18,12,5,0.97); border: 1px solid rgba(184,146,44,0.4);
  border-top: none; border-radius: 0 0 4px 4px; max-height: 240px; overflow-y: auto; z-index: 30;
  box-shadow: 2px 6px 18px rgba(0,0,0,0.7); }
.wsd-group { font-size: 9px; text-transform: uppercase; letter-spacing: 0.1em;
  color: #7a6a50; padding: 5px 10px 2px; border-top: 1px solid rgba(184,146,44,0.1); }
.wsd-group:first-child { border-top: none; }
.wsd-item { padding: 5px 12px; font-size: 12px; cursor: pointer; color: #c8b890;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wsd-item:hover { background: rgba(184,146,44,0.12); color: #e8dcc4; }
.wsd-empty { padding: 8px 12px; font-size: 11px; color: #5a4a30; font-style: italic; }
/* Travel time tab */
.tt-presets { display:flex; gap:3px; flex-wrap:wrap; }
.tt-preset { flex:1; min-width:0; padding:5px 3px; font-size:10px; letter-spacing:0.04em;
  text-transform:uppercase; background:#1a1408; border:1px solid rgba(184,146,44,0.2);
  color:#7a6a50; border-radius:2px; cursor:pointer; }
.tt-preset:hover { color:#c8a84a; border-color:rgba(184,146,44,0.45); }
.tt-preset.active { background:#0a0805; color:#e8dcc4; border-color:rgba(184,146,44,0.45);
  font-weight:bold; }
.tt-state { font-size:11px; color:#8a7a5a; margin-bottom:6px; min-height:14px; }
.tt-state b { color:#e8a060; font-weight:normal; }
.tt-stops-list { display:flex; flex-direction:column; gap:0; }
.tt-stop-row { display:flex; align-items:center; gap:6px; padding:4px 6px;
  background:#1a1408; border-radius:3px; border:1px solid rgba(184,146,44,0.12);
  margin-bottom:1px; }
.tt-stop-num { width:18px; height:18px; border-radius:50%; background:#3a5a3a;
  display:flex; align-items:center; justify-content:center;
  font-size:10px; font-weight:bold; color:#fff; flex-shrink:0; }
.tt-stop-name { flex:1; font-size:11px; color:#c8b87a; font-style:italic;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.tt-stop-rm { background:none; border:none; color:#5a4a30; cursor:pointer;
  font-size:11px; padding:0 2px; line-height:1; flex-shrink:0; }
.tt-stop-rm:hover { color:#e8a060; }
.tt-leg-row { padding:3px 6px 3px 30px; font-size:11px; display:grid;
  grid-template-columns:auto auto 1fr; gap:4px; align-items:center; color:#7a6a50; }
.tt-leg-row select { background:#1a1408; border:1px solid rgba(184,146,44,0.25);
  color:#c8b87a; padding:2px 3px; border-radius:2px; font-size:11px; min-width:0; }
.tt-leg-row select option { background:#1a1410; }
.tt-leg-row select option:disabled { color:#5a4a30; }
.tt-leg-res { color:#c8a84a; text-align:right; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; }
.tt-leg-row.fetching .tt-leg-txt { opacity:0.55; font-style:italic; }
.tt-leg-row.fallback .tt-leg-res { color:#e8a060; }
.tt-leg-cancel { background:none; border:1px solid rgba(184,146,44,0.3); color:#c8b87a;
  cursor:pointer; font-size:10px; padding:0 4px; margin-left:5px; border-radius:2px; }
.tt-leg-cancel:hover { color:#e8a060; border-color:#e8a060; }
.tt-totals { border-top:1px solid rgba(184,146,44,0.18); padding:6px 0 0;
  display:grid; grid-template-columns:60px 1fr 1fr; gap:3px; font-size:11px; }
.tt-saved { display:flex; flex-direction:column; gap:2px; }
.tt-saved-row { display:flex; align-items:center; gap:6px; padding:3px 6px;
  background:#1a1408; border:1px solid rgba(184,146,44,0.12); border-radius:3px;
  font-size:11px; color:#c8b87a; }
.tt-saved-row.current { border-color:rgba(232,160,96,0.55); }
.tt-saved-name { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.tt-saved-meta { color:#7a6a50; font-size:10px; white-space:nowrap; }
.tt-saved-meta.gm { color:#8a6a40; }
.tt-saved-row button { background:none; border:1px solid rgba(184,146,44,0.25); color:#8a7a5a;
  border-radius:2px; cursor:pointer; font-size:10px; padding:1px 5px; }
.tt-saved-row button:hover { color:#e8dcc4; border-color:rgba(184,146,44,0.55); }
.tt-saved-row button.armed { color:#e8a060; border-color:#b83c3c; }
.tt-tot-lbl { color:#7a6a50; padding-top:2px; }
.tt-tot-v { color:#c8b87a; font-family:monospace; }
.tt-tot-t { color:#e8dcc4; font-weight:bold; }
.tt-map-pin { width:22px; height:22px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; font-size:10px; font-weight:bold; color:#fff; cursor:grab;
  border:2px solid rgba(255,255,255,0.7); box-shadow:0 2px 6px rgba(0,0,0,0.5); }
/* Player share bar */
#player-share { display:none; align-items:center; gap:6px; padding:4px 10px;
  background:rgba(90,160,90,0.12); border-bottom:1px solid rgba(90,160,90,0.2);
  font-size:11px; color:#7ab07a; }
#player-share a { color:#8ad08a; font-family:monospace; font-size:10px;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
#player-share-copy { background:none; border:1px solid rgba(90,160,90,0.3);
  color:#7ab07a; padding:2px 6px; border-radius:2px; cursor:pointer; font-size:10px; }
#player-share-copy:hover { background:rgba(90,160,90,0.15); }
"""


def _build_panel_add_point(cat_options: str, region_options: str) -> str:
    return f"""
<div class="field-group">
  <label>Coordinates <span style="color:#5a4a30">(click map)</span></label>
  <div class="coord-row">
    <span>lat</span><input id="add-lat" type="text" readonly placeholder="—">
    <span>lon</span><input id="add-lon" type="text" readonly placeholder="—">
  </div>
</div>
<div class="field-group">
  <label>Name *</label>
  <input id="add-name" type="text" placeholder="Nur-Ata">
</div>
<div class="field-group">
  <label>Fantasy Name</label>
  <input id="add-fantasy" type="text" placeholder="optional">
</div>
<div class="field-group">
  <label>Category *</label>
  <select id="add-category">
    <option value="">— select —</option>
    {cat_options}
  </select>
</div>
<div class="field-group">
  <label>Region</label>
  <select id="add-region">
    <option value="">— none —</option>
    {region_options}
  </select>
</div>
<div class="field-group">
  <label>Visibility</label>
  <div class="radio-row">
    <label><input type="radio" name="add-vis" value="public" checked> public</label>
    <label><input type="radio" name="add-vis" value="gm_secrets"> gm_secrets</label>
  </div>
</div>
<div class="field-group">
  <label>Description</label>
  <textarea id="add-description" rows="2" placeholder="optional"></textarea>
</div>
<button id="add-create-btn" class="btn">Create Location</button>
<p id="add-status" class="hint" style="margin-top:6px;"></p>
<p class="hint" style="color:#5a4a30;">Requires devserver: <code>venv/bin/python utilities/devserver.py</code></p>
"""


def _build_panel_plan_route() -> str:
    return """
<p class="hint" style="color:#7a6a50;">Click location markers on the map to add waypoints.</p>
<ul id="route-queue-list"><li class="queue-empty">No waypoints yet.</li></ul>
<div class="btn-row">
  <button id="route-remove-btn" class="btn btn-sm btn-danger" disabled>Remove Last</button>
  <button id="route-clear-btn" class="btn btn-sm btn-danger" disabled>Clear All</button>
</div>
<div class="field-group" style="margin-top:8px;">
  <label>Route Name</label>
  <input id="route-name" type="text" placeholder="Northern Silk Road">
</div>
<div class="field-group">
  <label>Description</label>
  <textarea id="route-desc" rows="2" placeholder="optional"></textarea>
</div>
<div class="field-group">
  <label>Route Type</label>
  <select id="route-type">
    <option value="trade-route">Trade Route</option>
    <option value="pilgrimage">Pilgrimage</option>
    <option value="military">Military</option>
    <option value="other">Other</option>
  </select>
</div>
<div class="field-group">
  <label style="flex-direction:row;align-items:center;gap:8px;cursor:pointer;">
    <input type="checkbox" id="route-spur-cb" style="accent-color:#b8922c;">
    Spur route (branch)
  </label>
</div>
<button id="route-add-btn" class="btn" disabled>Add Route</button>
<p id="route-status" class="hint" style="margin-top:6px;"></p>
<p class="hint" style="color:#5a4a30;">Requires devserver: <code>venv/bin/python utilities/devserver.py</code><br>
Adds segments, snaps to roads, rebuilds workshop automatically.</p>
"""


def _build_panel_edit_coords() -> str:
    # Every canonical category must be selectable: _openFieldEditor leaves the select
    # untouched for an unlisted category and Save Fields would silently re-type it.
    type_opts = "\n".join(
        f'      <option value="{c}">{"POI" if c == "poi" else c.replace("-", " ").title()}</option>'
        for c in CATEGORIES
    )
    marker_opts = "\n".join(
        f'      <option value="{v}">{label}</option>'
        for v, label in [
            ("", "— auto (from type) —"),
            ("city", "city"), ("capital", "capital"), ("town", "town"),
            ("bridge", "bridge"), ("fortress", "fortress"), ("landmark", "landmark"),
            ("sacred-site", "sacred-site"), ("oasis", "oasis"), ("lake", "lake"),
            ("route-node", "route-node"), ("poi", "poi"), ("dungeon", "dungeon"),
            ("false", "false (hidden)"),
        ]
    )
    return f"""
<button id="edit-mode-btn" class="btn edit-toggle">Enable Edit Mode</button>
<p class="hint" style="margin-top:6px;">Click a marker to edit its fields. Use <em>Move Pin</em> to reposition coordinates.</p>
<p class="hint" style="color:#5a4a30;">Requires devserver: <code>venv/bin/python utilities/devserver.py</code></p>
<div id="ef-panel" class="hidden" style="margin-top:10px;border-top:1px solid rgba(184,146,44,0.2);padding-top:8px;">
  <div class="list-heading">Editing: <span id="ef-slug" style="color:#c8a84a;font-family:monospace;text-transform:none;letter-spacing:0"></span></div>
  <div class="field-group">
    <label>Real Name</label>
    <input id="ef-name" type="text">
  </div>
  <div class="field-group" style="margin-top:5px;">
    <label>Fantasy Name <span style="color:#5a4a30;text-transform:none;letter-spacing:0;">(blank = use real name)</span></label>
    <input id="ef-fantasy" type="text" placeholder="optional">
  </div>
  <div class="field-group" style="margin-top:5px;">
    <label>Type</label>
    <select id="ef-type">
{type_opts}
    </select>
  </div>
  <div class="field-group" style="margin-top:5px;">
    <label>Map Marker</label>
    <select id="ef-marker">
{marker_opts}
    </select>
  </div>
  <div class="field-group" style="margin-top:5px;">
    <label>Visibility</label>
    <div class="radio-row">
      <label><input type="radio" name="ef-vis" value="public" checked> public</label>
      <label><input type="radio" name="ef-vis" value="gm_secrets"> GM only</label>
    </div>
  </div>
  <div class="btn-row" style="margin-top:8px;">
    <button id="ef-save-btn" class="btn">Save Fields</button>
    <button id="ef-move-btn" class="btn btn-sm">Move Pin</button>
  </div>
  <p id="ef-status" class="hint" style="margin-top:5px;min-height:14px;"></p>
</div>
<div id="unsaved-section" class="hidden" style="margin-top:6px;">
  <div class="list-heading">Saved This Session</div>
  <ul id="unsaved-list"></ul>
</div>
<div class="rebuild-section">
  <div class="list-heading">Rebuild</div>
  <div class="btn-row">
    <button id="rebuild-locations-btn" class="btn btn-sm">Rebuild Locations</button>
    <button id="rebuild-workshop-btn" class="btn btn-sm">Rebuild Workshop</button>
  </div>
  <p id="api-status" class="hint" style="margin-top:6px;"></p>
</div>
"""


def _build_panel_reveal() -> str:
    return """
<p class="hint" style="color:#7a6a50;">Click a GM-only marker, or press <strong>+</strong> below, to stage it. Nothing is written until you apply.</p>
<div class="list-heading" style="margin-top:0;">Staged</div>
<ul id="rv-staged"><li class="queue-empty">Nothing staged.</li></ul>
<div class="btn-row">
  <button id="rv-apply-btn" class="btn" disabled>Apply 0 reveals</button>
  <button id="rv-clear-btn" class="btn btn-sm btn-danger" disabled>Clear</button>
</div>
<div id="rv-confirm" class="hidden">
  <div>Set these to <strong>public</strong>? Players will see them after the rebuild.</div>
  <ul id="rv-confirm-list"></ul>
  <div class="btn-row">
    <button id="rv-confirm-yes" class="btn btn-sm">Confirm reveal</button>
    <button id="rv-confirm-no" class="btn btn-sm">Cancel</button>
  </div>
</div>
<p id="rv-status" class="hint"></p>
<div class="list-heading">GM-only locations (<span id="rv-hidden-count">0</span>)</div>
<div class="field-group">
  <input id="rv-filter" type="text" placeholder="Filter by name, type or region…" autocomplete="off" spellcheck="false">
</div>
<ul id="rv-hidden"></ul>
<p class="hint" style="color:#5a4a30;">Gold ring = staged, green ring = already public. Earmarks are kept in this browser.<br>
Requires devserver: <code>venv/bin/python utilities/devserver.py</code></p>
"""


def _tt_presets_html() -> str:
    """Preset buttons for the Travel Time tab, one per mode in the shared table."""
    buttons = []
    for mode, spec in travel_time.SPEEDS.items():
        active = " active" if mode == travel_time.DEFAULT_MODE else ""
        buttons.append(
            f'<button class="tt-preset{active}" data-mode="{mode}" '
            f'data-kpd="{spec["kmpd"]}" data-fly="{1 if spec["fly"] else 0}">{spec["label"]}</button>'
        )
    return "\n    ".join(buttons)


def _build_panel_travel_time() -> str:
    html = """
<p class="hint" style="color:#7a6a50;margin-bottom:6px;">Click map or a location to add stops. Drag markers to reposition. Every leg has its own mode and path.</p>
<div id="tt-state" class="tt-state"></div>
<div id="tt-stops-list" class="tt-stops-list"></div>
<div id="tt-totals" class="tt-totals" hidden>
  <span class="tt-tot-lbl">Total</span>
  <span class="tt-tot-v" id="tt-tot-dist">—</span>
  <span class="tt-tot-t" id="tt-tot-time">—</span>
</div>
<div class="field-group" style="margin-top:8px;">
  <label>Mode for new legs / all legs</label>
  <div class="tt-presets">
    __TT_PRESETS__
  </div>
  <select id="tt-all-path">
    <option value="">Path: keep each leg's own</option>
    __TT_PATH_OPTS__
  </select>
</div>
<div class="field-group" style="margin-top:8px;">
  <label for="tt-name">Journey name</label>
  <input id="tt-name" type="text" maxlength="__TT_MAX_NAME__" placeholder="e.g. Spring caravan to Merv" autocomplete="off">
</div>
<div class="field-group" style="margin-top:6px;">
  <label for="tt-vis">Visible to players</label>
  <select id="tt-vis">
    <option value="gm_secrets">GM only</option>
    <option value="public">Players (once every stop is public)</option>
  </select>
</div>
<div class="btn-row" style="margin-top:8px;">
  <button id="tt-save-btn" class="btn btn-sm" disabled>Save</button>
  <button id="tt-saveas-btn" class="btn btn-sm" hidden>Save as new</button>
  <button id="tt-clear-btn" class="btn btn-sm btn-danger" hidden>Clear All</button>
</div>
<p id="tt-status" class="hint" style="margin-top:4px;min-height:14px;"></p>
<div class="field-group" style="margin-top:10px;">
  <label>Saved journeys</label>
  <div id="tt-saved" class="tt-saved"></div>
</div>
<p class="hint" style="color:#5a4a30;margin-top:8px;">Saved to <code>world/data/tarim-shaiel-journeys.geojson</code> via the devserver. Time is computed from length, mode and path; it is never stored.</p>
<p class="hint" style="color:#5a4a30;margin-top:6px;"><b>Terrain</b> walks the ground, not the roads: a least-cost path over elevation tiles, slower on slopes, with a per-mode slope limit (a cart refuses what a walker climbs). Rivers and lakes are not obstacles and existing roads are ignored. Limits and speeds are assumptions. Elevation: U.S. Geological Survey (SRTM, GMTED2010) via AWS Terrain Tiles; tiles are cached in this browser.</p>
"""
    path_opts = "\n    ".join(
        f'<option value="{p}">{p.capitalize()}</option>'
        for p in journeys.LEG_PATHS
    )
    return (html.replace("__TT_PRESETS__", _tt_presets_html())
                .replace("__TT_PATH_OPTS__", path_opts)
                .replace("__TT_MAX_NAME__", str(journeys.MAX_NAME)))


# Reveal tab: stage GM-only locations, then apply them together. Earmarks live in
# localStorage (per browser) and nothing touches a file until Apply. Raw string so
# the JS stays readable; it is spliced into _build_app_js after the field editor.
_REVEAL_JS = r"""
var _rvKey="_wsRevealStaged";
var _rvReady=false;
var _rvStaged=[];
var _rvErr={};
var _rvBusy=false;
var _rvListEl=document.getElementById("rv-staged");
var _rvHiddenEl=document.getElementById("rv-hidden");
var _rvFilterEl=document.getElementById("rv-filter");
var _rvCountEl=document.getElementById("rv-hidden-count");
var _rvApplyBtn=document.getElementById("rv-apply-btn");
var _rvClearBtn=document.getElementById("rv-clear-btn");
var _rvConfirmEl=document.getElementById("rv-confirm");
var _rvConfirmList=document.getElementById("rv-confirm-list");
var _rvStatusEl=document.getElementById("rv-status");
var _rvBadge=document.getElementById("rv-badge");

function _rvEsc(s){
  return String(s==null?"":s).replace(/[&<>"']/g,function(c){
    return{"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c];});
}
function _rvIsHidden(l){return !!l&&l.visibility!=="public";}
function _rvName(l){return l.label||l.title||l.slug;}
function _rvMeta(l){return (l.category||"")+(l.region?" · "+l.region:"");}
function _rvSetStatus(msg,cls){_rvStatusEl.textContent=msg;_rvStatusEl.className="hint"+(cls?" "+cls:"");}

function _rvLoad(){
  var raw=null,arr=[];
  try{raw=localStorage.getItem(_rvKey);}catch(e){}
  try{arr=JSON.parse(raw||"[]");}catch(e){}
  if(!Array.isArray(arr))arr=[];
  _rvStaged=arr.filter(function(s,i,a){return a.indexOf(s)===i&&_rvIsHidden(_locBySlug[s]);});
}
function _rvSave(){try{localStorage.setItem(_rvKey,JSON.stringify(_rvStaged));}catch(e){}}

function _rvUpdateRings(){
  var src;
  try{src=map.getSource("reveal-source");}catch(e){return;}
  if(!src)return;
  var feats=[];
  if(_activeTab==="reveal"){
    _locList.forEach(function(l){
      var st=_rvStaged.indexOf(l.slug)!==-1?"staged":(_rvIsHidden(l)?null:"public");
      if(st)feats.push({type:"Feature",properties:{state:st},
        geometry:{type:"Point",coordinates:[l.lon,l.lat]}});
    });
  }
  src.setData({type:"FeatureCollection",features:feats});
}

function _rvRenderHidden(){
  var q=_rvFilterEl.value.trim().toLowerCase();
  var all=_locList.filter(_rvIsHidden);
  var rows=all.filter(function(l){
    return !q||(l.label||"").toLowerCase().indexOf(q)!==-1||(l.title||"").toLowerCase().indexOf(q)!==-1||
      (l.category||"").toLowerCase().indexOf(q)!==-1||(l.region||"").toLowerCase().indexOf(q)!==-1;});
  _rvCountEl.textContent=q?rows.length+" of "+all.length:String(all.length);
  _rvHiddenEl.innerHTML=rows.length?rows.map(function(l){
    var staged=_rvStaged.indexOf(l.slug)!==-1;
    return '<li class="queue-item rv-item"><div class="rv-main">'+
      '<button class="rv-name" data-fly="'+_rvEsc(l.slug)+'">'+_rvEsc(_rvName(l))+'</button>'+
      '<div class="qi-dist">'+_rvEsc(_rvMeta(l))+'</div></div>'+
      '<button class="btn btn-sm rv-add" data-slug="'+_rvEsc(l.slug)+'"'+(staged?" disabled":"")+'>'+
      (staged?"staged":"+")+'</button></li>';}).join(""):
    '<li class="queue-empty">'+(all.length?"No matches.":"Every location is public.")+'</li>';
}

function _rvRefresh(){
  _rvSave();
  var n=_rvStaged.length;
  _rvApplyBtn.disabled=_rvBusy||n===0;
  _rvApplyBtn.textContent=n===1?"Apply 1 reveal":"Apply "+n+" reveals";
  _rvClearBtn.disabled=_rvBusy||n===0;
  if(n===0)_rvConfirmEl.classList.add("hidden");
  if(_rvBadge){_rvBadge.textContent=n;_rvBadge.classList.toggle("hidden",n===0);}
  _rvListEl.innerHTML=n?_rvStaged.map(function(s){
    var l=_locBySlug[s];
    var err=_rvErr[s]?'<div class="rv-err">✗ '+_rvEsc(_rvErr[s])+'</div>':"";
    return '<li class="queue-item rv-item"><div class="rv-main"><span class="qi-label">'+_rvEsc(_rvName(l))+
      '</span><div class="qi-dist">'+_rvEsc(_rvMeta(l))+'</div>'+err+'</div>'+
      '<button class="rv-x" data-slug="'+_rvEsc(s)+'" title="Unstage">✕</button></li>';}).join(""):
    '<li class="queue-empty">Nothing staged.</li>';
  _rvRenderHidden();
  _rvUpdateRings();
}

function _rvStage(slug){
  if(_rvBusy||!_rvIsHidden(_locBySlug[slug]))return;
  if(_rvStaged.indexOf(slug)===-1)_rvStaged.push(slug);
  delete _rvErr[slug];
  _rvConfirmEl.classList.add("hidden");
  _rvRefresh();
}
function _rvUnstage(slug){
  if(_rvBusy)return;
  _rvStaged=_rvStaged.filter(function(s){return s!==slug;});
  delete _rvErr[slug];
  _rvConfirmEl.classList.add("hidden");
  _rvRefresh();
}
function _rvToggleFromMap(slug){
  var l=_locBySlug[slug];
  if(!l)return;
  if(!_rvIsHidden(l)){_rvSetStatus(_rvName(l)+" is already public.","");return;}
  if(_rvStaged.indexOf(slug)!==-1)_rvUnstage(slug);else _rvStage(slug);
}

function _rvRebuild(target){
  return fetch("/api/rebuild/"+target,{method:"POST"})
    .then(function(r){return r.json();})
    .then(function(d){return !!d.ok;},function(){return false;});
}

function _rvApply(){
  if(_rvBusy||!_rvStaged.length)return;
  _rvBusy=true;
  _rvErr={};
  _rvConfirmEl.classList.add("hidden");
  var queue=_rvStaged.slice(),done=0,aborted=false;
  _rvSetStatus("Revealing 0 of "+queue.length+"…","");
  _rvRefresh();
  function step(i){
    if(i>=queue.length||aborted)return Promise.resolve();
    var slug=queue[i];
    return _patchFrontmatterRaw(slug,{visibility:"public"}).then(function(d){
      if(d&&d.ok){done++;_rvStaged=_rvStaged.filter(function(s){return s!==slug;});}
      else{_rvErr[slug]=(d&&d.error)||"error";}
      _rvSetStatus("Revealing "+(i+1)+" of "+queue.length+"…","");
    },function(){
      aborted=true;
      _rvErr[slug]="Network error — is the devserver running?";
    }).then(function(){return step(i+1);});
  }
  step(0).then(function(){
    _refreshLocSource();
    _rvBusy=false;
    var failed=queue.length-done;
    if(!done){
      _rvSetStatus("✗ Nothing revealed — "+failed+" failed.","err");
      _rvRefresh();
      return;
    }
    _rvSetStatus("Revealed "+done+(failed?" · "+failed+" failed":"")+". Rebuilding…","");
    _rvRefresh();
    _rvRebuild("workshop").then(function(okW){
      return _rvRebuild("locations").then(function(okL){return okW&&okL;});
    }).then(function(okAll){
      _rvSetStatus((okAll?"✓ ":"✗ ")+"Revealed "+done+(failed?" · "+failed+" failed":"")+
        (okAll?". Player map and location pages rebuilt.":". Rebuild failed — see the devserver log."),
        (okAll&&!failed)?"ok":"err");
    });
  });
}

_rvListEl.addEventListener("click",function(e){
  var b=e.target.closest(".rv-x");
  if(b)_rvUnstage(b.dataset.slug);
});
_rvHiddenEl.addEventListener("click",function(e){
  var a=e.target.closest(".rv-add");
  if(a){if(!a.disabled)_rvStage(a.dataset.slug);return;}
  var n=e.target.closest(".rv-name");
  if(n)_wsFlyTo(_locBySlug[n.dataset.fly]);
});
_rvFilterEl.addEventListener("input",_rvRenderHidden);
_rvClearBtn.addEventListener("click",function(){
  if(_rvBusy)return;
  _rvStaged=[];_rvErr={};_rvSetStatus("","");_rvRefresh();
});
_rvApplyBtn.addEventListener("click",function(){
  if(_rvBusy||!_rvStaged.length)return;
  _rvConfirmList.innerHTML=_rvStaged.map(function(s){
    return "<li>"+_rvEsc(_rvName(_locBySlug[s]))+"</li>";}).join("");
  _rvConfirmEl.classList.remove("hidden");
});
document.getElementById("rv-confirm-yes").addEventListener("click",_rvApply);
document.getElementById("rv-confirm-no").addEventListener("click",function(){
  _rvConfirmEl.classList.add("hidden");});

_rvLoad();
_rvReady=true;
_rvRefresh();
"""


# Travel tab: every leg between two stops carries its own mode and path; whole
# journeys save through the devserver (/api/journeys). Time is never stored, only
# computed from km, mode and path with the same table as shared/travel_time.py.
# Raw string like _REVEAL_JS; it is spliced into _build_app_js after the search box.
_TRAVEL_JS = r"""
var _ttStops=[];
var _ttLegs=[];
var _ttMarkers=[];
var _ttDefMode=_TT.defaultMode,_ttDefPath=_TT.defaultPath;
var _ttJid=null,_ttDirty=false,_ttSeq=0,_ttArmed=null,_ttArmTimer=null;
var _ttColors=["#3a6a3a","#3a4a8a","#7a3a3a","#6a5a20","#4a2a7a","#206a60","#7a4a20"];

function _ttEl(id){return document.getElementById(id);}
function _ttEsc(s){
  return String(s==null?"":s).replace(/[&<>"]/g,function(c){
    return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
function _ttSay(msg){var e=_ttEl("tt-status");if(e)e.textContent=msg||"";}
function _ttIsFly(m){var s=_TT.speeds[m];return !!(s&&s.fly);}
function _ttMarkDirty(){_ttDirty=true;}

// Same arithmetic as travel_time.segment_hours: fliers ignore the path factor.
function _ttHours(leg){
  var s=_TT.speeds[leg.mode];
  if(!s||!(leg.km>0))return 0;
  var pf=s.fly?1:(_TT.path[leg.path]||1);
  var kmph=s.kmpd/_TT.hours*pf*(leg.slope||1);
  return kmph>0?leg.km/kmph:0;
}
// Same wording as travel_time.format_duration: a day is _TT.hours of marching.
function _ttFmt(h){
  if(!(h>0))return "0 days";
  var d=h/_TT.hours;
  if(d<1)return Math.round(h)+" h";
  return (d<10?d.toFixed(1):Math.round(d))+" days";}
function _ttKm(km){return (km<10?km.toFixed(1):km.toFixed(0))+" km";}
function _ttLineKm(c){
  var k=0;
  for(var i=1;i<c.length;i++)k+=_haversineKm(c[i-1][0],c[i-1][1],c[i][0],c[i][1]);
  return k;}

function _ttPinEl(n,color){
  var el=document.createElement("div");
  el.className="tt-map-pin";el.textContent=n;el.style.background=color;
  return el;}

function _ttArm(token){
  _ttArmed=token;
  clearTimeout(_ttArmTimer);
  _ttArmTimer=setTimeout(function(){_ttArmed=null;_ttRenderSaved();},4000);
  _ttRenderSaved();}
function _ttDisarm(){_ttArmed=null;clearTimeout(_ttArmTimer);}

function _ttFind(id){
  var fs=_journeyGJ.features;
  for(var i=0;i<fs.length;i++){if(fs[i].id===id)return fs[i];}
  return null;}

// -- Legs ---------------------------------------------------------------
function _ttNewLeg(prev){
  return {mode:prev?prev.mode:_ttDefMode,path:prev?prev.path:_ttDefPath,
    coords:[],km:0,roadCache:null,terrainCache:{},progress:"",state:"ok",note:"",
    pathKeep:prev?prev.pathKeep:null,slope:1,tok:0};}

// A terrain route depends on the mode only through its slope limit, so routes
// are cached per limit. "" for fliers, which never use the terrain path.
function _ttSlopeKey(mode){
  var m=_TT.terrain.maxSlope[mode];
  return m==null?"":String(m);}

// Set a leg's mode. Fliers are always straight; the path is remembered and
// restored when the mode goes back to a walker. True when the geometry has to
// be rebuilt: the path changed, or a terrain leg now has a different slope limit.
function _ttApplyMode(leg,mode){
  var wasFly=_ttIsFly(leg.mode),fly=_ttIsFly(mode),old=leg.path,oldKey=_ttSlopeKey(leg.mode);
  leg.mode=mode;
  if(fly&&!wasFly){leg.pathKeep=leg.path;leg.path="straight";}
  else if(!fly&&wasFly){leg.path=leg.pathKeep||_ttDefPath;leg.pathKeep=null;}
  return leg.path!==old||(leg.path==="terrain"&&_ttSlopeKey(mode)!==oldKey);}

function _ttRoadFailed(leg){
  var i=_ttLegs.indexOf(leg);
  if(i<0)return;
  var a=_ttStops[i],b=_ttStops[i+1];
  leg.path="straight";leg.state="ok";
  leg.coords=[[a.lng,a.lat],[b.lng,b.lat]];leg.km=_ttLineKm(leg.coords);
  leg.note="road routing unavailable, straight line used";
  _ttSay("Leg "+(i+1)+": road routing is unavailable, so it falls back to a straight line.");}

function _ttFetchRoad(leg,a,b,tok){
  var url="https://router.project-osrm.org/route/v1/foot/"+a.lng+","+a.lat+";"+b.lng+","+b.lat+
    "?geometries=geojson&overview=full";
  fetch(url).then(function(r){return r.json();}).then(function(d){
    if(leg.tok!==tok||_ttLegs.indexOf(leg)<0)return;
    if(d.code==="Ok"&&d.routes&&d.routes.length){
      leg.roadCache={coords:d.routes[0].geometry.coordinates,km:d.routes[0].distance/1000};
      leg.coords=leg.roadCache.coords;leg.km=leg.roadCache.km;leg.state="ok";
    }else{_ttRoadFailed(leg);}
    _ttRender();
  }).catch(function(){
    if(leg.tok!==tok||_ttLegs.indexOf(leg)<0)return;
    _ttRoadFailed(leg);_ttRender();});}

// -- Terrain routing (#312) ---------------------------------------------
// One Web Worker (terrain_path.js, embedded as _TERRAIN_SRC) routes one leg at a
// time and the rest wait in a queue. Stopping a job terminates the worker, which
// also aborts its tile requests; the next job starts a fresh one.
var _ttWorker=null,_ttWorkerUrl=null,_ttQueue=[],_ttCur=null,_ttJobSeq=0;

function _ttKillWorker(){
  if(_ttWorker){try{_ttWorker.terminate();}catch(e){}_ttWorker=null;}}

function _ttWorkerStart(){
  if(_ttWorker)return _ttWorker;
  try{
    if(!_ttWorkerUrl)_ttWorkerUrl=URL.createObjectURL(new Blob([_TERRAIN_SRC],{type:"text/javascript"}));
    _ttWorker=new Worker(_ttWorkerUrl);
  }catch(e){_ttWorker=null;return null;}
  _ttWorker.onmessage=_ttWorkerMsg;
  _ttWorker.onerror=function(ev){
    if(ev&&ev.preventDefault)ev.preventDefault();
    var job=_ttCur;
    _ttKillWorker();_ttCur=null;
    if(job&&!_ttJobStale(job)){_ttTerrainFailed(job.leg,"The terrain worker failed");_ttRender();}
    else _ttPump();};
  return _ttWorker;}

function _ttJobStale(j){return j.leg.tok!==j.tok||_ttLegs.indexOf(j.leg)<0;}

// Drop queued jobs whose leg changed or went away; stop a running one the same way.
function _ttSweepJobs(){
  _ttQueue=_ttQueue.filter(function(j){return !_ttJobStale(j);});
  if(_ttCur&&_ttJobStale(_ttCur)){_ttKillWorker();_ttCur=null;}
  _ttPump();}

function _ttPump(){
  if(_ttCur)return;
  var j=_ttQueue.shift();
  while(j&&_ttJobStale(j))j=_ttQueue.shift();
  if(!j)return;
  var w=_ttWorkerStart();
  if(!w){_ttTerrainFailed(j.leg,"Terrain routing is not available in this browser");_ttRender();return;}
  _ttCur=j;
  j.leg.progress="starting";_ttShowProgress(j.leg);
  w.postMessage({type:"route",id:j.id,from:j.from,to:j.to,maxSlope:j.maxSlope,cfg:_TT.terrain});}

function _ttQueueTerrain(leg,a,b,tok,key){
  _ttQueue.push({id:++_ttJobSeq,leg:leg,tok:tok,key:key,
    from:[a.lng,a.lat],to:[b.lng,b.lat],maxSlope:_TT.terrain.maxSlope[leg.mode]});
  _ttPump();}

function _ttWorkerMsg(ev){
  var m=ev.data,job=_ttCur;
  if(!m||!job||m.id!==job.id)return;
  var leg=job.leg;
  if(m.type==="progress"){
    leg.progress=m.phase==="tiles"?"tiles "+m.done+"/"+m.total:
      "searching "+(m.done/1e6).toFixed(1)+"M cells";
    _ttShowProgress(leg);
    return;}
  _ttCur=null;
  if(!_ttJobStale(job)){
    if(m.type==="result"){
      var km=_ttLineKm(m.coords);
      // average speed on the route relative to flat ground (1 = no slowdown)
      var sf=Math.min(2,Math.max(0.05,Math.round(m.pathKm/m.costKm*10000)/10000));
      leg.terrainCache[job.key]={coords:m.coords,km:km,slope:sf};
      leg.coords=m.coords;leg.km=km;leg.slope=sf;
      leg.state="ok";leg.progress="";leg.note="";
    }else{_ttTerrainFailed(leg,m.message||"Terrain routing failed");}
    _ttRender();}
  _ttPump();}

function _ttShowProgress(leg){
  var i=_ttLegs.indexOf(leg);
  if(i<0)return;
  var el=document.querySelector('.tt-leg-row[data-leg="'+i+'"] .tt-leg-txt');
  if(el)el.textContent="terrain: "+leg.progress;}

function _ttTerrainFailed(leg,msg){
  var i=_ttLegs.indexOf(leg);
  if(i<0)return;
  var a=_ttStops[i],b=_ttStops[i+1];
  leg.path="straight";leg.state="ok";leg.slope=1;leg.progress="";
  leg.coords=[[a.lng,a.lat],[b.lng,b.lat]];leg.km=_ttLineKm(leg.coords);
  leg.note=msg+" (straight line used)";
  _ttSay("Leg "+(i+1)+": "+msg+". It falls back to a straight line.");}

function _ttCancelTerrain(leg){
  if(_ttCur&&_ttCur.leg===leg){_ttKillWorker();_ttCur=null;}
  _ttQueue=_ttQueue.filter(function(j){return j.leg!==leg;});
  leg.tok=++_ttSeq;
  _ttTerrainFailed(leg,"Terrain routing cancelled");
  _ttRender();}

// Rebuild one leg's geometry from its stops, mode and path. Road and terrain legs
// reuse their cached route when there is one; otherwise they show a straight line
// while the request runs, so a mode change never triggers a request on its own.
function _ttSetLegGeom(i){
  var leg=_ttLegs[i],a=_ttStops[i],b=_ttStops[i+1];
  if(!leg||!a||!b)return;
  var tok=++_ttSeq;leg.tok=tok;leg.note="";leg.progress="";
  var straight=[[a.lng,a.lat],[b.lng,b.lat]];
  var fly=_ttIsFly(leg.mode);
  if(leg.path==="road"&&!fly){
    leg.slope=1;
    if(leg.roadCache){
      leg.coords=leg.roadCache.coords;leg.km=leg.roadCache.km;leg.state="ok";
    }else{
      leg.coords=straight;leg.km=_ttLineKm(straight);leg.state="fetching";
      _ttFetchRoad(leg,{lng:a.lng,lat:a.lat},{lng:b.lng,lat:b.lat},tok);}
  }else if(leg.path==="terrain"&&!fly){
    var key=_ttSlopeKey(leg.mode),hit=leg.terrainCache[key];
    if(hit){
      leg.coords=hit.coords;leg.km=hit.km;leg.slope=hit.slope;leg.state="ok";
    }else{
      leg.coords=straight;leg.km=_ttLineKm(straight);leg.slope=1;
      leg.state="fetching";leg.progress="queued";
      _ttQueueTerrain(leg,a,b,tok,key);}
  }else{
    leg.slope=1;
    leg.coords=straight;leg.km=_ttLineKm(straight);leg.state="ok";}
  _ttRender();}

function _ttRecalc(i){
  if(!_ttLegs[i])return;
  _ttLegs[i].roadCache=null;_ttLegs[i].terrainCache={};
  _ttSetLegGeom(i);}

function _ttSetMode(i,mode){
  var leg=_ttLegs[i];
  if(!leg||!_TT.speeds[mode])return;
  var rebuild=_ttApplyMode(leg,mode);
  _ttMarkDirty();
  if(rebuild)_ttSetLegGeom(i);else _ttRender();}

function _ttSetPath(i,path){
  var leg=_ttLegs[i];
  if(!leg||_ttIsFly(leg.mode)||leg.path===path)return;
  leg.path=path;
  _ttMarkDirty();
  _ttSetLegGeom(i);}

// -- Stops --------------------------------------------------------------
function _ttAddMarker(i){
  var s=_ttStops[i];
  var el=_ttPinEl(i+1,_ttColors[i%_ttColors.length]);
  var mk=new maplibregl.Marker({element:el,draggable:true}).setLngLat([s.lng,s.lat]).addTo(map);
  mk.on("dragend",function(){
    var idx=_ttMarkers.indexOf(mk);
    if(idx<0)return;
    var p=mk.getLngLat();
    _ttStops[idx]={lng:p.lng,lat:p.lat,name:p.lat.toFixed(2)+","+p.lng.toFixed(2),slug:null};
    _ttMarkDirty();
    if(idx>0)_ttRecalc(idx-1);
    if(idx<_ttLegs.length)_ttRecalc(idx);
    _ttRender();});
  _ttMarkers.push(mk);}

function _ttSetPt(lng,lat,name,slug){
  if(_ttStops.length>=_JRN.maxStops){_ttSay("A journey can have at most "+_JRN.maxStops+" stops.");return;}
  var i=_ttStops.length;
  _ttStops.push({lng:lng,lat:lat,name:name||(lat.toFixed(2)+","+lng.toFixed(2)),slug:slug||null});
  _ttAddMarker(i);
  _ttMarkDirty();
  if(i>0){
    _ttLegs.push(_ttNewLeg(_ttLegs[i-2]||null));
    _ttSetLegGeom(i-1);
  }else{_ttRender();}}

function _ttRemoveStop(i){
  var n=_ttStops.length;
  if(i<0||i>=n)return;
  _ttStops.splice(i,1);
  _ttMarkers[i].remove();_ttMarkers.splice(i,1);
  var merged=-1;
  if(n<=1){_ttLegs=[];}
  else if(i===0){_ttLegs.shift();}
  else if(i===n-1){_ttLegs.pop();}
  else{
    // an interior stop: its two legs become one, keeping the earlier leg's mode and path
    _ttLegs.splice(i,1);merged=i-1;}
  _ttMarkers.forEach(function(mk,j){
    var el=mk.getElement();
    if(el){el.textContent=j+1;el.style.background=_ttColors[j%_ttColors.length];}});
  _ttMarkDirty();
  if(merged>=0)_ttRecalc(merged);else _ttRender();}

function _ttClear(){
  _ttMarkers.forEach(function(mk){mk.remove();});
  _ttStops=[];_ttLegs=[];_ttMarkers=[];
  _ttJid=null;_ttDirty=false;_ttDisarm();
  _ttEl("tt-name").value="";_ttEl("tt-vis").value="gm_secrets";
  _ttSay("");_ttFilterSaved();_ttRender();_ttRenderSaved();}

// -- Rendering ----------------------------------------------------------
function _ttLegRowHtml(i){
  var leg=_ttLegs[i];
  if(!leg)return "";
  var fly=_ttIsFly(leg.mode),mo="",po="";
  Object.keys(_TT.speeds).forEach(function(m){
    mo+='<option value="'+m+'"'+(m===leg.mode?' selected':'')+'>'+_ttEsc(_TT.speeds[m].label)+'</option>';});
  Object.keys(_TT.path).forEach(function(p){
    po+='<option value="'+p+'"'+(p===leg.path?' selected':'')+'>'+
      p.charAt(0).toUpperCase()+p.slice(1)+'</option>';});
  var fetching=leg.state==="fetching",terr=fetching&&leg.path==="terrain";
  var res=fetching?(terr?"terrain: "+(leg.progress||"queued"):"fetching road…"):
    (leg.note?"⚠ ":"")+_ttKm(leg.km)+" · "+_ttFmt(_ttHours(leg));
  var tip=leg.note||(leg.path==="terrain"&&!fly&&leg.slope!==1?
    "Terrain slope factor ×"+leg.slope.toFixed(2)+" (average speed against flat ground)":"");
  return '<div class="tt-leg-row'+(fetching?' fetching':'')+(leg.note?' fallback':'')+
    '" data-leg="'+i+'">'+
    '<select class="tt-leg-mode" title="Mode of travel for this leg">'+mo+'</select>'+
    '<select class="tt-leg-path" title="Path for this leg"'+(fly?' disabled':'')+'>'+po+'</select>'+
    '<span class="tt-leg-res" title="'+_ttEsc(tip)+'"><span class="tt-leg-txt">'+_ttEsc(res)+'</span>'+
    (terr?'<button class="tt-leg-cancel" title="Cancel terrain routing and use a straight line">cancel</button>':'')+
    '</span></div>';}

function _ttUpdateLine(){
  var src=map.getSource("tt-line");
  if(!src)return;
  src.setData({type:"FeatureCollection",features:_ttLegs.filter(function(l){return l.coords.length>=2;})
    .map(function(l){return {type:"Feature",properties:{},geometry:{type:"LineString",coordinates:l.coords}};})});}

function _ttRenderState(){
  var st=_ttEl("tt-state");
  if(!st)return;
  var f=_ttJid?_ttFind(_ttJid):null;
  if(_ttJid)st.innerHTML="Editing <b>"+_ttEsc(f?f.properties.name:_ttJid)+"</b>"+(_ttDirty?" — unsaved changes":"");
  else if(_ttStops.length)st.textContent="New journey — not saved yet";
  else st.textContent="New journey — add two or more stops";
  var busy=_ttLegs.some(function(l){return l.state==="fetching";});
  var save=_ttEl("tt-save-btn"),as=_ttEl("tt-saveas-btn");
  save.disabled=_ttStops.length<2||busy;
  save.textContent=_ttJid?"Save changes":"Save";
  as.hidden=!_ttJid;as.disabled=save.disabled;}

function _ttRender(){
  var list=_ttEl("tt-stops-list");
  if(!list)return;
  _ttSweepJobs();
  var html="";
  _ttStops.forEach(function(s,i){
    html+='<div class="tt-stop-row"><div class="tt-stop-num" style="background:'+
      _ttColors[i%_ttColors.length]+'">'+(i+1)+'</div>'+
      '<span class="tt-stop-name">'+_ttEsc(s.name)+'</span>'+
      '<button class="tt-stop-rm" data-i="'+i+'" title="Remove this stop">✕</button></div>';
    if(i<_ttStops.length-1)html+=_ttLegRowHtml(i);});
  list.innerHTML=html;
  list.querySelectorAll(".tt-stop-rm").forEach(function(b){
    b.addEventListener("click",function(){_ttRemoveStop(parseInt(b.dataset.i,10));});});
  list.querySelectorAll(".tt-leg-row").forEach(function(row){
    var i=parseInt(row.dataset.leg,10);
    row.querySelector(".tt-leg-mode").addEventListener("change",function(){_ttSetMode(i,this.value);});
    row.querySelector(".tt-leg-path").addEventListener("change",function(){_ttSetPath(i,this.value);});
    var cx=row.querySelector(".tt-leg-cancel");
    if(cx)cx.addEventListener("click",function(){_ttCancelTerrain(_ttLegs[i]);});});
  var tot=_ttEl("tt-totals"),km=0,h=0,wait=false;
  if(tot)tot.hidden=_ttStops.length<2;
  _ttLegs.forEach(function(l){if(l.state==="fetching")wait=true;km+=l.km;h+=_ttHours(l);});
  _ttEl("tt-tot-dist").textContent=wait?"…":_ttKm(km);
  _ttEl("tt-tot-time").textContent=wait?"…":_ttFmt(h);
  _ttEl("tt-clear-btn").hidden=_ttStops.length===0;
  _ttUpdateLine();
  _ttRenderState();}

// -- Saved journeys -----------------------------------------------------
// Mirror of journeys.journey_is_public for the live Workshop dimming only;
// the player build decides for real when it is rebuilt.
function _ttApproxPublic(props){
  if(props.visibility!=="public")return false;
  var st=props.stops||[];
  for(var i=0;i<st.length;i++){
    var s=st[i],near=null,best=1e9;
    if(s.slug){var L=_locBySlug[s.slug];if(!L||L.visibility==="gm_secrets")return false;}
    for(var j=0;j<_locList.length;j++){
      var q=_locList[j];
      if(q.lat==null||q.lon==null)continue;
      var d=_haversineKm(s.lng,s.lat,q.lon,q.lat);
      if(d<best){best=d;near=q;}}
    if(near&&best<=1.0&&near.visibility==="gm_secrets")return false;}
  return true;}

function _ttSyncSrc(){
  var s=map.getSource("journeys");
  if(s)s.setData(_journeyGJ);}

function _ttFilterSaved(){
  var flt=["!=",["get","id"],_ttJid||""];
  ["journeys","journeys-hit"].forEach(function(l){if(map.getLayer(l))map.setFilter(l,flt);});}

function _ttStore(f,popup){
  f.properties=f.properties||{};
  f.properties.id=f.id;
  f.properties._playerVisible=_ttApproxPublic(f.properties);
  var fs=_journeyGJ.features,k=-1;
  for(var i=0;i<fs.length;i++){if(fs[i].id===f.id){k=i;break;}}
  if(k>=0)fs[k]=f;else fs.push(f);
  _jrnInfo[f.id]=popup;
  _ttSyncSrc();}

function _ttRenderSaved(){
  var box=_ttEl("tt-saved");
  if(!box)return;
  var fs=_journeyGJ.features.slice().sort(function(a,b){
    return String(a.properties.name||"").localeCompare(String(b.properties.name||""));});
  if(!fs.length){box.innerHTML='<span class="hint">No saved journeys yet.</span>';return;}
  var html="";
  fs.forEach(function(f){
    var id=f.id,info=_jrnInfo[id]||{},gm=f.properties.visibility!=="public";
    var armLoad=_ttArmed==="load:"+id,armDel=_ttArmed==="del:"+id;
    html+='<div class="tt-saved-row'+(id===_ttJid?' current':'')+'" data-id="'+_ttEsc(id)+'">'+
      '<span class="tt-saved-name" title="'+_ttEsc(f.properties.name)+'">'+_ttEsc(f.properties.name)+'</span>'+
      '<span class="tt-saved-meta'+(gm?' gm':'')+'">'+(gm?'GM only':'public')+
      (info.total?' · '+_ttEsc(info.total):'')+'</span>'+
      '<button class="tt-load'+(armLoad?' armed':'')+'">'+(armLoad?'Discard &amp; load':'Load')+'</button>'+
      '<button class="tt-del'+(armDel?' armed':'')+'">'+(armDel?'Confirm?':'Delete')+'</button></div>';});
  box.innerHTML=html;
  box.querySelectorAll(".tt-saved-row").forEach(function(row){
    var id=row.dataset.id;
    row.querySelector(".tt-load").addEventListener("click",function(){_ttLoad(id);});
    row.querySelector(".tt-del").addEventListener("click",function(){_ttDelete(id);});});}

function _ttFit(){
  var pts=[];
  _ttLegs.forEach(function(l){l.coords.forEach(function(c){pts.push(c);});});
  if(pts.length<2)return;
  var b=new maplibregl.LngLatBounds(pts[0],pts[0]);
  pts.forEach(function(c){b.extend(c);});
  map.fitBounds(b,{padding:80,maxZoom:9,duration:600});}

function _ttLoad(id){
  var f=_ttFind(id);
  if(!f)return;
  if(_ttDirty&&_ttStops.length&&_ttArmed!=="load:"+id){
    _ttArm("load:"+id);
    _ttSay("The working journey has unsaved changes. Click Discard & load to replace it.");
    return;}
  _ttDisarm();
  var p=f.properties,lines=(f.geometry&&f.geometry.coordinates)||[];
  _ttMarkers.forEach(function(mk){mk.remove();});
  _ttMarkers=[];_ttStops=[];_ttLegs=[];
  (p.stops||[]).forEach(function(s){
    _ttStops.push({lng:s.lng,lat:s.lat,name:s.name,slug:s.slug||null});});
  (p.legs||[]).forEach(function(l,i){
    var a=_ttStops[i],b=_ttStops[i+1];
    var c=(lines[i]&&lines[i].length>=2)?lines[i]:[[a.lng,a.lat],[b.lng,b.lat]];
    var mode=_TT.speeds[l.mode]?l.mode:_TT.defaultMode;
    var km=_ttLineKm(c);
    var walk=!_ttIsFly(mode),sf=l.slope_factor||1,tc={};
    if(l.path==="terrain"&&walk)tc[_ttSlopeKey(mode)]={coords:c,km:km,slope:sf};
    _ttLegs.push({mode:mode,path:l.path,coords:c,km:km,
      roadCache:(l.path==="road"&&walk)?{coords:c,km:km}:null,terrainCache:tc,progress:"",
      state:"ok",note:"",pathKeep:null,slope:sf,tok:0});});
  // A stop tied to a location follows it: if the location moved since the
  // journey was saved, snap the stop to it and redo the legs on either side.
  var moved=[],gone=[];
  _ttStops.forEach(function(s,i){
    if(!s.slug)return;
    var L=_locBySlug[s.slug];
    if(!L||L.lat==null||L.lon==null){gone.push(s.name);return;}
    if(_haversineKm(s.lng,s.lat,L.lon,L.lat)>_JRN.staleM/1000){s.lng=L.lon;s.lat=L.lat;moved.push(i);}});
  _ttStops.forEach(function(s,i){_ttAddMarker(i);});
  var redo={};
  moved.forEach(function(i){if(i>0)redo[i-1]=1;if(i<_ttLegs.length)redo[i]=1;});
  _ttJid=id;_ttDirty=moved.length>0;
  _ttEl("tt-name").value=p.name||"";
  _ttEl("tt-vis").value=p.visibility==="public"?"public":"gm_secrets";
  _ttFilterSaved();_ttRender();_ttRenderSaved();
  Object.keys(redo).forEach(function(k){_ttRecalc(parseInt(k,10));});
  _ttFit();
  var msg="Loaded “"+p.name+"”.";
  if(moved.length)msg+=" "+moved.length+" stop(s) moved since it was saved, so "+Object.keys(redo).length+
    " leg(s) were recomputed (unsaved).";
  if(gone.length)msg+=" Location no longer on the map for: "+gone.join(", ")+" (kept at the saved position).";
  _ttSay(msg);}

function _ttSave(asNew){
  if(_ttStops.length<2)return;
  var nameEl=_ttEl("tt-name"),name=(nameEl.value||"").trim();
  if(!name){_ttSay("Name the journey first.");nameEl.focus();return;}
  if(_ttLegs.some(function(l){return l.state==="fetching";})){
    _ttSay("Routing is still running. Save when the legs have finished.");return;}
  var upd=_ttJid&&!asNew;
  var body={name:name,visibility:_ttEl("tt-vis").value,
    stops:_ttStops.map(function(s){
      var o={lng:s.lng,lat:s.lat,name:s.name};if(s.slug)o.slug=s.slug;return o;}),
    legs:_ttLegs.map(function(l){
      var o={mode:l.mode,path:l.path,coords:l.coords};
      if(l.slope&&l.slope!==1)o.slope_factor=l.slope;return o;})};
  fetch(upd?"/api/journeys/"+encodeURIComponent(_ttJid):"/api/journeys",{
    method:upd?"PUT":"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,d:d};});})
  .then(function(x){
    if(!x.ok||!x.d.ok){_ttSay((x.d&&x.d.error)||"Save failed.");return;}
    _ttStore(x.d.journey,x.d.popup);
    _ttJid=x.d.journey.id;_ttDirty=false;_ttDisarm();
    _ttFilterSaved();_ttRender();_ttRenderSaved();
    _ttSay("Saved “"+name+"”.");})
  .catch(function(){_ttSay("Devserver not reachable. Run venv/bin/python utilities/devserver.py");});}

function _ttDelete(id){
  var f=_ttFind(id);
  if(!f)return;
  if(_ttArmed!=="del:"+id){
    _ttArm("del:"+id);
    _ttSay("Click Confirm? to delete “"+f.properties.name+"” permanently.");
    return;}
  _ttDisarm();
  fetch("/api/journeys/"+encodeURIComponent(id),{method:"DELETE"})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,d:d};});})
  .then(function(x){
    if(!x.ok||!x.d.ok){_ttSay((x.d&&x.d.error)||"Delete failed.");_ttRenderSaved();return;}
    _journeyGJ.features=_journeyGJ.features.filter(function(g){return g.id!==id;});
    delete _jrnInfo[id];
    _ttSyncSrc();
    if(_ttJid===id){_ttJid=null;_ttDirty=true;}
    _ttFilterSaved();_ttRender();_ttRenderSaved();
    _ttSay("Deleted “"+f.properties.name+"”.");})
  .catch(function(){_ttSay("Devserver not reachable. Run venv/bin/python utilities/devserver.py");});}

// -- Controls -----------------------------------------------------------
document.querySelectorAll(".tt-preset").forEach(function(btn){
  btn.addEventListener("click",function(){
    var mode=btn.dataset.mode;
    document.querySelectorAll(".tt-preset").forEach(function(b){b.classList.toggle("active",b===btn);});
    _ttDefMode=mode;
    var redo=[];
    _ttLegs.forEach(function(leg,i){
      if(leg.mode===mode)return;
      if(_ttApplyMode(leg,mode))redo.push(i);
      _ttMarkDirty();});
    _ttRender();
    redo.forEach(_ttSetLegGeom);});});

_ttEl("tt-all-path").addEventListener("change",function(){
  var p=this.value;
  this.value="";
  if(!p)return;
  _ttDefPath=p;
  _ttLegs.forEach(function(leg,i){
    if(_ttIsFly(leg.mode)){leg.pathKeep=p;return;}
    if(leg.path===p)return;
    leg.path=p;_ttMarkDirty();_ttSetLegGeom(i);});
  _ttRender();});

_ttEl("tt-name").addEventListener("input",function(){
  if(_ttStops.length||_ttJid)_ttMarkDirty();
  _ttRenderState();});

_ttEl("tt-vis").addEventListener("change",function(){
  if(!_ttJid)return;
  var want=this.value,id=_ttJid;
  fetch("/api/journeys/"+encodeURIComponent(id),{method:"PATCH",
    headers:{"Content-Type":"application/json"},body:JSON.stringify({visibility:want})})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,d:d};});})
  .then(function(x){
    if(!x.ok||!x.d.ok){_ttSay((x.d&&x.d.error)||"Could not change visibility.");return;}
    _ttStore(x.d.journey,x.d.popup);_ttRenderSaved();_ttRenderState();
    _ttSay(want==="public"?"Marked public. It reaches the player map once every stop is a public location and the maps are rebuilt.":
      "Marked GM only.");})
  .catch(function(){_ttSay("Devserver not reachable. Run venv/bin/python utilities/devserver.py");});});

_ttEl("tt-save-btn").addEventListener("click",function(){_ttSave(false);});
_ttEl("tt-saveas-btn").addEventListener("click",function(){_ttSave(true);});
_ttEl("tt-clear-btn").addEventListener("click",_ttClear);

var _jrnTog=_ttEl("jrn-toggle");
if(_jrnTog)_jrnTog.addEventListener("change",function(){
  var v=this.checked?"visible":"none";
  ["journeys","journeys-hit"].forEach(function(l){if(map.getLayer(l))map.setLayoutProperty(l,"visibility",v);});});

_ttRender();
_ttRenderSaved();

fetch("/api/journeys").then(function(r){return r.ok?r.json():null;}).then(function(d){
  if(!d||!d.features)return;
  _journeyGJ.features=[];
  d.features.forEach(function(f){_ttStore(f,(d.popups||{})[f.id]||{});});
  _ttFilterSaved();_ttRenderSaved();}).catch(function(){});
"""


def _build_app_js(style_url: str, icons_js: str, maptiler_key: str = "") -> str:
    # Build as string concatenation to avoid f-string {{ }} escaping for JS blocks.
    # fmt: off
    return (
        # -- Utility --
        'function _haversineKm(lon1,lat1,lon2,lat2){'
        'var R=6371,d=Math.PI/180,dlat=(lat2-lat1)*d,dlon=(lon2-lon1)*d;'
        'var a=Math.sin(dlat/2)*Math.sin(dlat/2)+Math.cos(lat1*d)*Math.cos(lat2*d)*Math.sin(dlon/2)*Math.sin(dlon/2);'
        'return R*2*Math.asin(Math.sqrt(a));}\n'

        'function _copyText(text,btnEl){'
        'navigator.clipboard.writeText(text).then(function(){'
        'var prev=btnEl.textContent;btnEl.textContent="Copied!";'
        'setTimeout(function(){btnEl.textContent=prev;},900);});}\n'

        # -- Slug → location lookup (for Tab 2 queue) --
        'var _locBySlug={};\n'
        '_locList.forEach(function(l){_locBySlug[l.slug]=l;});\n'

        # Mirror route feature id into properties — MapLibre click events don't
        # reliably surface a string top-level `id` back on e.features[0].id
        '_routeGJ.features.forEach(function(f){if(f.id)f.properties._route_id=f.id;});\n'

        # -- Active tab state --
        # Restore last active tab across reloads triggered by add/delete actions,
        # or a manual refresh, so the workshop doesn't snap back to "Add Point"
        # every time.
        'var _wsSavedTab=null;\n'
        'try{_wsSavedTab=sessionStorage.getItem("_wsTab");}catch(e){}\n'
        'var _activeTab=_wsSavedTab||"add-point";\n'

        # -- Icon type visibility --
        'var _typeEnabled={'
        '"city":true,"capital":true,"bridge":true,"landmark":true,"fortress":true,'
        '"town":true,"sacred-site":true,"oasis":true,"lake":true,"route-node":true,"poi":true'
        '};\n'
        'try{'
        'var _itss=sessionStorage.getItem("_wsIt");'
        'if(_itss){var _itsv=JSON.parse(_itss);'
        'Object.keys(_itsv).forEach(function(k){if(k in _typeEnabled)_typeEnabled[k]=_itsv[k];});}'
        '}catch(_e){}\n'
        'var _tierCats={'
        '"locations-major":["city","capital","bridge","landmark","fortress"],'
        '"locations-towns":["town"],'
        '"locations-secondary":["oasis","lake"],'
        '"locations-spiritual":["sacred-site"],'
        '"locations-routes":["route-node"],'
        '"locations-detail":["poi"]'
        '};\n'
        'function _rebuildTierFilters(){'
        'Object.keys(_tierCats).forEach(function(lyr){'
        'var on=_tierCats[lyr].filter(function(c){return _typeEnabled[c];});'
        'if(on.length===0){'
        'map.setLayoutProperty(lyr,"visibility","none");'
        '}else{'
        'map.setLayoutProperty(lyr,"visibility","visible");'
        'var eqs=on.map(function(c){return["==",["get","category"],c];});'
        'var catF=on.length===1?eqs[0]:["any"].concat(eqs);'
        'map.setFilter(lyr,["all",catF,["!=",["get","mapMarker"],false]]);'
        '}'
        '});'
        'try{sessionStorage.setItem("_wsIt",JSON.stringify(_typeEnabled));}catch(_e){}}\n'

        # -- Map init --
        # Restore last view (center/zoom) across the same reloads.
        'var _wsSavedCenter=null,_wsSavedZoom=null;\n'
        'try{'
        'var _wsSc=sessionStorage.getItem("_wsCenter");'
        'var _wsSz=sessionStorage.getItem("_wsZoom");'
        'if(_wsSc&&_wsSz){_wsSavedCenter=JSON.parse(_wsSc);_wsSavedZoom=parseFloat(_wsSz);}'
        '}catch(e){}\n'

        'var map=new maplibregl.Map({'
        'container:"map",'
        'style:"' + style_url + '",'
        'center:_wsSavedCenter||[75.0,40.0],'
        'zoom:_wsSavedZoom!=null?_wsSavedZoom:5,'
        'minZoom:3,'
        'maxZoom:18'
        '});\n'

        'window.addEventListener("beforeunload",function(){'
        'try{'
        'var ctr=map.getCenter();'
        'sessionStorage.setItem("_wsCenter",JSON.stringify([ctr.lng,ctr.lat]));'
        'sessionStorage.setItem("_wsZoom",String(map.getZoom()));'
        'sessionStorage.setItem("_wsTab",_activeTab);'
        '}catch(e){}'
        '});\n'

        # -- Tab switching --
        'function _setTab(tab){'
        '_activeTab=tab;'
        'document.querySelectorAll(".tab-btn").forEach(function(b){'
        'b.classList.toggle("active",b.dataset.tab===tab);});'
        'document.querySelectorAll(".panel").forEach(function(p){'
        'p.classList.toggle("active",p.id==="panel-"+tab);});'
        # Clear Tab 2 highlights when switching away
        'if(tab!=="plan-route")_clearHighlights();'
        'if(typeof _rvReady!=="undefined"&&_rvReady)_rvUpdateRings();'
        '}\n'
        'document.querySelectorAll(".tab-btn").forEach(function(b){'
        'b.addEventListener("click",function(){_setTab(b.dataset.tab);});});\n'
        # Apply the restored (or default) tab now that _setTab exists — the
        # server-rendered HTML always marks "Add Point" active by default.
        '_setTab(_activeTab);\n'

        # -- Tab 1: coordinate picker --
        'var _addLat=document.getElementById("add-lat");'
        'var _addLon=document.getElementById("add-lon");'
        'var _addName=document.getElementById("add-name");'
        'var _addFantasy=document.getElementById("add-fantasy");'
        'var _addCat=document.getElementById("add-category");'
        'var _addRegion=document.getElementById("add-region");'
        'var _addDesc=document.getElementById("add-description");\n'

        # mouseup: set coords when Tab 1 is active
        'map.on("mouseup",function(e){'
        'if(_activeTab!=="add-point")return;'
        '_addLat.value=e.lngLat.lat.toFixed(6);'
        '_addLon.value=e.lngLat.lng.toFixed(6);'
        '});\n'

        'var _addCreateBtn=document.getElementById("add-create-btn");'
        'var _addStatus=document.getElementById("add-status");\n'

        '_addCreateBtn.addEventListener("click",function(){'
        'var lat=_addLat.value,lon=_addLon.value;'
        'var name=_addName.value.trim();'
        'var cat=_addCat.value;'
        'if(!lat||!lon||!name||!cat){alert("Fill in: coordinates (click map), Name, and Category.");return;}'
        'var body={'
        '"name":name,"lat":parseFloat(lat),"lon":parseFloat(lon),"category":cat,'
        '"fantasy_name":_addFantasy.value.trim(),'
        '"region":_addRegion.value,'
        '"visibility":(document.querySelector("input[name=\'add-vis\']:checked")||{value:"public"}).value,'
        '"description":_addDesc.value.trim()'
        '};'
        '_addStatus.textContent="Creating...";'
        '_addCreateBtn.disabled=true;'
        'fetch("/api/locations/create",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})'
        '.then(function(r){return r.json();})'
        '.then(function(d){'
        '_addCreateBtn.disabled=false;'
        'if(d.ok){'
        '_addStatus.textContent="Created. Rebuilding GeoJSON and workshop…";'
        'fetch("/api/rebuild/workshop",{method:"POST"}).then(function(){_addStatus.textContent="Done — reload to see new pin.";});'
        '}else{'
        '_addStatus.textContent="Error: "+(d.error||d.output||"unknown");'
        '}})'
        '.catch(function(e){_addCreateBtn.disabled=false;_addStatus.textContent="Devserver not running.";});'
        '});\n'

        # -- Tab 2: route planner --
        'var _queue=[];\n'
        'var _routeQueueList=document.getElementById("route-queue-list");'
        'var _routeRemoveBtn=document.getElementById("route-remove-btn");'
        'var _routeClearBtn=document.getElementById("route-clear-btn");'
        'var _routeAddBtn=document.getElementById("route-add-btn");'
        'var _routeStatus=document.getElementById("route-status");'
        'var _routeSpurCb=document.getElementById("route-spur-cb");'
        'var _routeNameEl=document.getElementById("route-name");'
        'var _routeDescEl=document.getElementById("route-desc");'
        'var _routeTypeEl=document.getElementById("route-type");\n'

        'function _updateQueueDisplay(){'
        'var enabled=_queue.length>0;'
        '_routeRemoveBtn.disabled=!enabled;'
        '_routeClearBtn.disabled=!enabled;'
        'var canExport=_queue.length>=2;'
        '_routeAddBtn.disabled=!canExport;'
        # Auto-suggest route name from first/last slugs if field is empty
        'if(canExport&&!_routeNameEl.value.trim()){'
        'var first=_queue[0].label,last=_queue[_queue.length-1].label;'
        '_routeNameEl.placeholder=first+" → "+last;'
        '}'
        'if(!enabled){'
        '_routeQueueList.innerHTML=\'<li class="queue-empty">No waypoints yet.</li>\';'
        '_routeNameEl.placeholder="Northern Silk Road";'
        'return;}'
        '_routeQueueList.innerHTML=_queue.map(function(item,i){'
        'var distStr="";'
        'if(i>0){'
        'var prev=_queue[i-1];'
        'var km=_haversineKm(prev.lon,prev.lat,item.lon,item.lat);'
        'var days=Math.ceil(km/30);'
        'distStr=\'<div class="qi-dist">~\'+Math.round(km)+\' km / \'+days+(days===1?" day":" days")+\'</div>\';}'
        'return \'<li class="queue-item"><span class="qi-num">\'+(i+1)+\'.</span>\'+'
        '\'<span class="qi-label">\'+item.label+\'</span>\'+distStr+\'</li>\';'
        '}).join("");'
        '}\n'

        'function _clearHighlights(){'
        'if(map.getSource("highlight-source")){'
        'map.getSource("highlight-source").setData({type:"FeatureCollection",features:[]});}'
        '}\n'

        'function _updateHighlights(){'
        'if(!map.getSource("highlight-source"))return;'
        'var features=_queue.map(function(item,i){'
        'return{type:"Feature",properties:{index:i+1},'
        'geometry:{type:"Point",coordinates:[item.lon,item.lat]}};});'
        'map.getSource("highlight-source").setData({type:"FeatureCollection",features:features});'
        # Update preview polyline
        'if(map.getSource("route-preview")){'
        'if(_queue.length>=2){'
        'var coords=_queue.map(function(item){return[item.lon,item.lat];});'
        'map.getSource("route-preview").setData({type:"FeatureCollection",'
        'features:[{type:"Feature",properties:{},'
        'geometry:{type:"LineString",coordinates:coords}}]});'
        '}else{'
        'map.getSource("route-preview").setData({type:"FeatureCollection",features:[]});'
        '}}'
        '}\n'

        'function _addToQueue(slug){'
        'var loc=_locBySlug[slug];'
        'if(!loc)return;'
        '_queue.push({slug:loc.slug,label:loc.label||loc.title,lat:loc.lat,lon:loc.lon});'
        '_updateQueueDisplay();'
        '_updateHighlights();'
        '}\n'

        '_routeRemoveBtn.addEventListener("click",function(){'
        '_queue.pop();_updateQueueDisplay();_updateHighlights();});\n'

        '_routeClearBtn.addEventListener("click",function(){'
        '_queue=[];_updateQueueDisplay();_updateHighlights();});\n'

        '_routeAddBtn.addEventListener("click",function(){'
        'if(_queue.length<2)return;'
        'var slugs=_queue.map(function(i){return i.slug;});'
        'var body={slugs:slugs,spur:_routeSpurCb.checked,'
        'name:_routeNameEl.value.trim(),description:_routeDescEl.value.trim(),'
        'routeType:_routeTypeEl.value};'
        '_routeStatus.textContent="Adding route…";'
        '_routeAddBtn.disabled=true;'
        'fetch("/api/routes/add",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})'
        '.then(function(r){return r.json();})'
        '.then(function(d){'
        '_routeAddBtn.disabled=false;'
        'if(d.ok){'
        '_routeStatus.textContent="Route added. Rebuilding workshop…";'
        'fetch("/api/rebuild/workshop",{method:"POST"}).then(function(){_routeStatus.textContent="Done — reload to see new route.";});'
        '}else{'
        '_routeStatus.textContent="Error: "+(d.error||d.output||"unknown");'
        '}})'
        '.catch(function(e){_routeAddBtn.disabled=false;_routeStatus.textContent="Devserver not running.";});'
        '});\n'

        # -- Map load --
        'map.on("load",function(){\n'

        # Raster overlays — hidden by default, sit below all custom data
        'var _topoTiles=["https://api.maptiler.com/maps/topo-v2/{z}/{x}/{y}.png?key='
        + maptiler_key +
        '"];'
        'map.addSource("topo-overlay",{type:"raster",tiles:_topoTiles,tileSize:256,'
        'attribution:"© MapTiler"});\n'
        'map.addLayer({id:"topo-overlay",type:"raster",source:"topo-overlay",'
        'layout:{visibility:"none"},paint:{"raster-opacity":0.55}});\n'
        'var _satTiles=["https://api.maptiler.com/tiles/satellite-v2/{z}/{x}/{y}.jpg?key='
        + maptiler_key +
        '"];'
        'map.addSource("sat-overlay",{type:"raster",tiles:_satTiles,tileSize:256,'
        'attribution:"© MapTiler"});\n'
        'map.addLayer({id:"sat-overlay",type:"raster",source:"sat-overlay",'
        'layout:{visibility:"none"},paint:{"raster-opacity":0.6}});\n'

        # Region overlay
        'map.addSource("regions",{type:"geojson",data:_regionGJ});\n'
        + map_style.regions_layers_js() +

        # Routes
        'map.addSource("routes",{type:"geojson",data:_routeGJ});\n'
        + map_style.routes_layer_js(dim_hidden=True) +

        # Saved journeys (solid), dimmed while not yet player-visible
        'map.addSource("journeys",{type:"geojson",data:_journeyGJ});\n'
        + map_style.journeys_layer_js(dim_hidden=True) +

        # Route-selected highlight layer (orange)
        'map.addSource("route-selected",{type:"geojson",data:{type:"FeatureCollection",features:[]}});\n'
        'map.addLayer({id:"route-selected",type:"line",minzoom:4,source:"route-selected",'
        'paint:{"line-color":"#e05a2b","line-width":5,"line-opacity":0.95}});\n'

        # Route cursor + click-to-select
        'map.on("mousemove","routes",function(){map.getCanvas().style.cursor="pointer";});\n'
        'map.on("mouseleave","routes",function(){map.getCanvas().style.cursor="";});\n'
        'map.on("click","routes",function(e){'
        'var f=e.features[0];'
        'map.getSource("route-selected").setData({type:"FeatureCollection",features:[f]});'
        '_showRoutePanel(f);'
        '});\n'
        'map.on("click",function(e){'
        'if(_activeTab==="travel-time"&&!map.queryRenderedFeatures(e.point,{layers:_locLayerIds||[]}).length){'
        '_ttSetPt(e.lngLat.lng,e.lngLat.lat,null);}'
        'if(!map.queryRenderedFeatures(e.point,{layers:["routes"]}).length){'
        'if(map.getSource("route-selected")){'
        'map.getSource("route-selected").setData({type:"FeatureCollection",features:[]});}'
        '_hideRoutePanel();}'
        '});\n'

        # Icons + location symbol layers
        + icons_js +
        'map.addSource("locations",{type:"geojson",data:_locGJ});\n'

        # icon_match expression + six-tier location layers (shared with the player map)
        + map_style.location_tiers_js() +

        # Highlight source/layer for Tab 2 selected markers
        'map.addSource("highlight-source",{type:"geojson",data:{type:"FeatureCollection",features:[]}});\n'
        'map.addLayer({id:"highlight-circles",type:"circle",source:"highlight-source",'
        'paint:{"circle-radius":16,"circle-color":"rgba(0,0,0,0)",'
        '"circle-stroke-width":3,"circle-stroke-color":"#f5d060","circle-stroke-opacity":0.9}});\n'

        # Reveal tab rings: gold = staged, green = already public (only filled
        # while the Reveal tab is open — see _rvUpdateRings)
        'map.addSource("reveal-source",{type:"geojson",data:{type:"FeatureCollection",features:[]}});\n'
        'map.addLayer({id:"reveal-rings",type:"circle",source:"reveal-source",'
        'paint:{"circle-radius":13,"circle-color":"rgba(0,0,0,0)","circle-stroke-width":'
        '["case",["==",["get","state"],"staged"],3.5,2],'
        '"circle-stroke-color":["case",["==",["get","state"],"staged"],"#f5d060","#6a9a2c"],'
        '"circle-stroke-opacity":0.95}});\n'

        # Route preview polyline for Tab 2 waypoint builder
        'map.addSource("route-preview",{type:"geojson",data:{type:"FeatureCollection",features:[]}});\n'
        'map.addLayer({id:"route-preview-line",type:"line",source:"route-preview",'
        'layout:{"line-cap":"round","line-join":"round"},'
        'paint:{"line-color":"#f5d060","line-width":2.5,"line-opacity":0.85,"line-dasharray":[3,3]}});\n'

        # Shared hover popup (title, type, description, GM-only badge), then the
        # Workshop's own click handlers across all location tiers
        + map_style.hover_popup_js(gm_badge=True) +
        # Journey line popups (same text the player map shows); the working
        # journey in the Travel tab is drawn separately by tt-line
        map_style.journey_hover_js() +
        '_locLayerIds.forEach(function(lyr){'
        'map.on("click",lyr,function(e){'
        'var p=e.features[0].properties;'
        'var slug=p._slug||p.slug||"";'
        'if(_activeTab==="travel-time"){'
        'var coords=e.features[0].geometry.coordinates;'
        'var name=p.title||p.label||slug||"";'
        '_ttSetPt(coords[0],coords[1],name,slug);return;}'
        'if(!slug)return;'
        'if(_activeTab==="reveal"){_rvToggleFromMap(slug);return;}'
        'if(_activeTab==="plan-route"){_addToQueue(slug);return;}'
        'if(_activeTab==="edit-coords"&&_editMode){'
        '_openFieldEditor(e.features[0]);}'
        '});});\n'

        # Overlay toggle + opacity wiring (sessionStorage-persisted)
        'function _wireOverlay(toggleId,opacityId,layerId,ssOn,ssOp,defaultOp){'
        'var tog=document.getElementById(toggleId),opc=document.getElementById(opacityId);'
        'try{'
        'var sv=sessionStorage.getItem(ssOn),so=sessionStorage.getItem(ssOp);'
        'if(sv==="1"){tog.checked=true;map.setLayoutProperty(layerId,"visibility","visible");}'
        'if(so!=null){opc.value=so;map.setPaintProperty(layerId,"raster-opacity",parseFloat(so)/100);}'
        '}catch(e){}'
        'tog.addEventListener("change",function(){'
        'map.setLayoutProperty(layerId,"visibility",tog.checked?"visible":"none");'
        'try{sessionStorage.setItem(ssOn,tog.checked?"1":"0");}catch(e){}});'
        'opc.addEventListener("input",function(){'
        'map.setPaintProperty(layerId,"raster-opacity",parseInt(opc.value)/100);'
        'try{sessionStorage.setItem(ssOp,opc.value);}catch(e){}});}'
        '_wireOverlay("topo-toggle","topo-opacity","topo-overlay","_wsTopoOn","_wsTopoOp",55);'
        '_wireOverlay("sat-toggle","sat-opacity","sat-overlay","_wsSatOn","_wsSatOp",60);'

        # Error handler: auto-uncheck offending overlay, set visibility none, show badge
        'function _showOverlayErr(toggleId,status){'
        'var tog=document.getElementById(toggleId);if(!tog)return;'
        'var lbl=tog.closest("label");if(!lbl)return;'
        'var prev=lbl.querySelector(".overlay-err");if(prev)prev.remove();'
        'var b=document.createElement("span");b.className="overlay-err";'
        'b.dataset.status=status!=null?String(status):"";'
        'b.title=status?"Layer failed to load (HTTP "+status+")":"Layer failed to load";'
        'b.textContent="⚠ "+(status||"ERR");'
        'lbl.appendChild(b);}'

        'map.on("error",function(e){'
        'var src=e&&e.sourceId;'
        'var _cfg={"topo-overlay":"topo-toggle","sat-overlay":"sat-toggle"};'
        'if(!src||!_cfg[src])return;'
        'var status=e.error&&(e.error.status||e.error.statusCode||null);'
        'var tid=_cfg[src];'
        'var tog=document.getElementById(tid);if(!tog)return;'
        'tog.checked=false;'
        'map.setLayoutProperty(src,"visibility","none");'
        'try{sessionStorage.setItem("_ws"+src+"On","0");}catch(_){}'
        '_showOverlayErr(tid,status);});\n'

        # Zoom readout (subheader)
        'var _zvv=document.getElementById("ws-zoom-val");'
        'function _updateZoom(){if(_zvv)_zvv.textContent=map.getZoom().toFixed(2);}'
        '_updateZoom();'
        'map.on("zoom",_updateZoom);\n'

        # Layers dropdown toggle
        '(function(){'
        'var _lb=document.getElementById("layers-btn");'
        'var _ld=document.getElementById("layers-dropdown");'
        '_lb.addEventListener("click",function(e){'
        'e.stopPropagation();'
        'var open=_ld.hidden;'
        '_ld.hidden=!open;'
        '_lb.classList.toggle("open",!open);'
        '});'
        'document.addEventListener("click",function(e){'
        'if(!_ld.hidden&&!_ld.contains(e.target)&&e.target!==_lb){'
        '_ld.hidden=true;_lb.classList.remove("open");}'
        '});'
        '})();\n'

        # Apply saved icon-type toggle state after layers are created
        '_rebuildTierFilters();\n'

        # Travel tab working journey: one dashed LineString per leg
        'map.addSource("tt-line",{type:"geojson",data:{type:"FeatureCollection",features:[]}});\n'
        'map.addLayer({id:"tt-line-layer",type:"line",source:"tt-line",'
        'layout:{"line-cap":"round","line-join":"round"},'
        'paint:{"line-color":"#e8a060","line-width":2.5,"line-opacity":0.9,"line-dasharray":[4,3]}});\n'

        'map.addControl(new maplibregl.ScaleControl({maxWidth:100,unit:"metric"}),"bottom-left");\n'

        '});\n'  # end map.on('load')

        # Wire icon type checkboxes (can run before or after map load)
        'document.querySelectorAll(".it-cb").forEach(function(cb){'
        'if(cb.dataset.type in _typeEnabled)cb.checked=_typeEnabled[cb.dataset.type];'
        'cb.addEventListener("change",function(){'
        '_typeEnabled[cb.dataset.type]=cb.checked;'
        '_rebuildTierFilters();'
        '});});\n'

        # Route Index: fly-to on row click (uses _routeGJ which is available immediately)
        'document.querySelectorAll("#panel-route-index .ri-row").forEach(function(row){'
        'row.addEventListener("click",function(e){'
        'if(e.target.closest(".ri-check"))return;'
        'var routeId=row.dataset.id;'
        'var feat=_routeGJ.features.find(function(f){return f.id===routeId;});'
        'if(!feat)return;'
        'var coords=feat.geometry.coordinates;'
        'var lons=coords.map(function(c){return c[0];});'
        'var lats=coords.map(function(c){return c[1];});'
        'var minLon=Math.min.apply(null,lons),maxLon=Math.max.apply(null,lons);'
        'var minLat=Math.min.apply(null,lats),maxLat=Math.max.apply(null,lats);'
        'document.querySelectorAll(".ri-row").forEach(function(r){r.classList.remove("active");});'
        'row.classList.add("active");'
        '_setTab("route-index");'
        'map.fitBounds([[minLon,minLat],[maxLon,maxLat]],{padding:60,duration:800});'
        '});});\n'

        # Route Index: select-all checkbox + delete-bulk button
        'document.getElementById("ri-select-all").addEventListener("change",function(e){'
        'document.querySelectorAll(".ri-cb").forEach(function(cb){cb.checked=e.target.checked;});'
        '_updateDeleteBtn();'
        '});\n'
        'document.querySelectorAll(".ri-cb").forEach(function(cb){'
        'cb.addEventListener("change",_updateDeleteBtn);'
        '});\n'
        'function _updateDeleteBtn(){'
        'var checked=Array.prototype.slice.call(document.querySelectorAll(".ri-cb:checked"));'
        'var btn=document.getElementById("ri-delete-btn");'
        'btn.hidden=checked.length===0;'
        'btn.textContent="🗑 Delete Selected ("+checked.length+")";'
        '}\n'
        'document.getElementById("ri-delete-btn").addEventListener("click",function(){'
        'var ids=Array.prototype.slice.call(document.querySelectorAll(".ri-cb:checked")).map(function(cb){return cb.dataset.id;});'
        'if(!ids.length)return;'
        'if(!confirm("Delete "+ids.length+" route(s)?"))return;'
        'fetch("/api/routes/delete-bulk",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ids:ids})})'
        '.then(function(r){return r.json();})'
        '.then(function(d){'
        'if(!d.ok){alert("Delete failed: "+(d.error||"unknown"));return;}'
        'fetch("/api/rebuild/workshop",{method:"POST"}).then(function(){location.reload();});'
        '})'
        '.catch(function(){alert("Devserver not running.");});'
        '});\n'

        # Route panel (map click) functions + button listeners
        'var _selectedRouteId=null;\n'
        'function _routeFeat(id){return _routeGJ.features.find(function(f){return f.id===id;});}\n'
        'function _routeKm(f){var c=f.geometry.coordinates,t=0;'
        'for(var i=0;i<c.length-1;i++)t+=_haversineKm(c[i][0],c[i][1],c[i+1][0],c[i+1][1]);return t;}\n'
        # Hours for a route by its mode, as travel_time.segment_hours (2-point routes are straight cuts)
        'function _routeHours(f){var m=_TT.speeds[f.properties.mode]?f.properties.mode:_TT.defaultMode,'
        'sp=_TT.speeds[m],pf=sp.fly?1:(_TT.path[f.geometry.coordinates.length<=2?"straight":"road"]||1);'
        'return _routeKm(f)/(sp.kmpd/_TT.hours*pf);}\n'
        'function _fmtHours(h,approx){var p=approx?"~":"",d=h/_TT.hours;'
        'if(d<1)return p+Math.round(h)+" h";return p+(d<10?d.toFixed(1):Math.round(d))+" days";}\n'
        'function _refreshRoutePanel(){'
        'var f=_routeFeat(_selectedRouteId);if(!f)return;var pr=f.properties;'
        'document.getElementById("route-panel-label").textContent=pr.route_name||pr.label||_selectedRouteId||"";'
        'var v=pr.visibility==="public"?"public":"gm_secrets";'
        'document.getElementById("route-panel-vis").value=v;'
        'document.getElementById("route-panel-mode").value=_TT.speeds[pr.mode]?pr.mode:_TT.defaultMode;'
        'var approx=f.geometry.coordinates.length<=2;'
        'document.getElementById("route-panel-time").textContent='
        '(approx?"~":"")+Math.round(_routeKm(f))+" km · "+_fmtHours(_routeHours(f),approx);'
        'var seen=document.getElementById("route-panel-seen");'
        'seen.className=pr._playerVisible?"rp-yes":(v==="public"?"rp-held":"");'
        'seen.textContent=pr._playerVisible?"Players see this route":'
        '(v==="public"?"Held: an end location is still hidden":"GM only");'
        '}\n'
        'function _showRoutePanel(feature){'
        '_selectedRouteId=feature.id||feature.properties._route_id||"";'
        '_refreshRoutePanel();'
        'document.getElementById("route-panel").hidden=false;'
        '}\n'
        # PATCH one property; on success mirror it into the in-page data and refresh the file on disk.
        'function _patchRoute(prop,value){'
        'var f=_routeFeat(_selectedRouteId);if(!f)return;'
        'var id=_selectedRouteId,body={};body[prop]=value;'
        'fetch("/api/routes/"+encodeURIComponent(id),{method:"PATCH",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})'
        '.then(function(r){return r.json();})'
        '.then(function(d){'
        'if(!d.ok){alert("Update failed: "+(d.error||"unknown"));_refreshRoutePanel();return;}'
        'f.properties[prop]=value;'
        'f.properties._playerVisible=!!f.properties._endsPublic&&f.properties.visibility==="public";'
        'map.getSource("routes").setData(_routeGJ);'
        '_refreshRoutePanel();_refreshRouteRow(f);'
        'fetch("/api/rebuild/workshop",{method:"POST"});'
        '})'
        '.catch(function(){alert("Devserver not running.");_refreshRoutePanel();});'
        '}\n'
        'function _refreshRouteRow(f){'
        'var row=document.querySelector(\'#panel-route-index .ri-row[data-id="\'+f.id+\'"]\');if(!row)return;'
        'var cells=row.querySelectorAll("td"),approx=f.geometry.coordinates.length<=2,'
        'm=_TT.speeds[f.properties.mode]?f.properties.mode:_TT.defaultMode;'
        'cells[4].innerHTML=_fmtHours(_routeHours(f),approx)+\' <span class="ri-mode">\'+_TT.speeds[m].label+\'</span>\';'
        'var pv=f.properties._playerVisible,pub=f.properties.visibility==="public";'
        'cells[5].innerHTML=pv?\'<span class="ri-vis ri-vis-pub">players</span>\':'
        '(pub?\'<span class="ri-vis ri-vis-held">held</span>\':\'<span class="ri-vis ri-vis-gm">GM</span>\');'
        '}\n'
        'document.getElementById("route-panel-vis").addEventListener("change",function(){_patchRoute("visibility",this.value);});\n'
        'document.getElementById("route-panel-mode").addEventListener("change",function(){_patchRoute("mode",this.value);});\n'
        'function _hideRoutePanel(){'
        '_selectedRouteId=null;'
        'document.getElementById("route-panel").hidden=true;'
        '}\n'
        'document.getElementById("route-panel-close").addEventListener("click",_hideRoutePanel);\n'
        'document.getElementById("route-panel-regenerate").addEventListener("click",function(){'
        'if(!_selectedRouteId)return;'
        'var btn=document.getElementById("route-panel-regenerate");'
        'btn.disabled=true;btn.textContent="🔄 Regenerating…";'
        'fetch("/api/routes/"+encodeURIComponent(_selectedRouteId)+"/regenerate",{method:"POST"})'
        '.then(function(r){return r.json();})'
        '.then(function(d){'
        'if(!d.ok){alert("Regenerate failed: "+(d.error||d.output||"unknown"));btn.disabled=false;btn.textContent="🔄 Regenerate";return;}'
        'fetch("/api/rebuild/workshop",{method:"POST"}).then(function(){location.reload();});'
        '})'
        '.catch(function(){alert("Devserver not running.");btn.disabled=false;btn.textContent="🔄 Regenerate";});'
        '});\n'
        'document.getElementById("route-panel-delete").addEventListener("click",function(){'
        'if(!_selectedRouteId)return;'
        'if(!confirm("Delete route \\""+_selectedRouteId+"\\"?"))return;'
        'fetch("/api/routes/"+encodeURIComponent(_selectedRouteId),{method:"DELETE"})'
        '.then(function(r){return r.json();})'
        '.then(function(d){'
        'if(!d.ok){alert("Delete failed: "+(d.error||"unknown"));return;}'
        'fetch("/api/rebuild/workshop",{method:"POST"}).then(function(){location.reload();});'
        '})'
        '.catch(function(){alert("Devserver not running.");});'
        '});\n'

        # -- Edit Coords panel --
        'var _editMode=false;\n'
        'var _pendingEdits={};\n'
        'var _dragMarker=null;\n'
        'var _editModeBtn=document.getElementById("edit-mode-btn");'
        'var _editBadge=document.getElementById("edit-badge");'
        'var _wsEditDot=document.getElementById("ws-edit-dot");'
        'var _unsavedSection=document.getElementById("unsaved-section");'
        'var _unsavedList=document.getElementById("unsaved-list");'
        'var _rebuildLocBtn=document.getElementById("rebuild-locations-btn");'
        'var _rebuildWsBtn=document.getElementById("rebuild-workshop-btn");'
        'var _apiStatus=document.getElementById("api-status");\n'

        # Devserver health check — retry once after 1 s to survive single-threaded server races
        '(function(){'
        'var _ban=document.getElementById("ds-banner");'
        'document.getElementById("ds-banner-close").addEventListener("click",function(){'
        '_ban.hidden=true;});'
        'function _chk(){return fetch("/api/health").then(function(r){return r.ok;});}'
        '_chk().then(function(ok){if(ok){_ban.hidden=true;}else{'
        'setTimeout(function(){_chk().then(function(ok2){_ban.hidden=ok2;}).catch(function(){_ban.hidden=false;});},1000);}}'
        ').catch(function(){setTimeout(function(){'
        '_chk().then(function(ok2){_ban.hidden=ok2;}).catch(function(){_ban.hidden=false;});},1000);});'
        '})();\n'

        'function _setApiStatus(msg,cls){'
        '_apiStatus.textContent=msg;'
        '_apiStatus.className="hint";'
        'if(cls)_apiStatus.classList.add(cls);'
        '}\n'

        '_editModeBtn.addEventListener("click",function(){'
        '_editMode=!_editMode;'
        '_editModeBtn.textContent=_editMode?"✓ Edit Mode ON":"Enable Edit Mode";'
        '_editModeBtn.classList.toggle("active",_editMode);'
        'if(_wsEditDot)_wsEditDot.classList.toggle("hidden",!_editMode);'
        'if(!_editMode&&_dragMarker){_dragMarker.remove();_dragMarker=null;}'
        'map.getCanvas().style.cursor=_editMode?"crosshair":"";'
        '});\n'

        'function _startDragEdit(slug,lngLat){'
        'if(_dragMarker){_dragMarker.remove();_dragMarker=null;}'
        'var el=document.createElement("div");'
        'el.className="drag-edit-marker";'
        '_dragMarker=new maplibregl.Marker({element:el,draggable:true})'
        '.setLngLat(lngLat).addTo(map);'
        '_dragMarker.on("dragend",function(){'
        'var ll=_dragMarker.getLngLat();'
        '_showConfirmPopover(slug,ll);'
        '});'
        '}\n'

        'function _showConfirmPopover(slug,lngLat){'
        'var lat=lngLat.lat.toFixed(6);'
        'var lon=lngLat.lng.toFixed(6);'
        'var html=\'<div class="ts-popup"><div class="ts-popup__title">\'+slug+\'</div>\''
        '+\'<div class="ts-popup__type" style="font-family:monospace">\'+lat+\', \'+lon+\'</div>\''
        '+\'<div style="display:flex;gap:6px;margin-top:8px;">\''
        '+\'<button id="ec-save" style="padding:4px 12px;background:#1a2a0a;border:1px solid #6a9a2c;color:#a8d840;font-size:11px;cursor:pointer;border-radius:2px;">Save</button>\''
        '+\'<button id="ec-cancel" style="padding:4px 10px;background:#2a1e08;border:1px solid rgba(184,146,44,0.3);color:#9a8a6a;font-size:11px;cursor:pointer;border-radius:2px;">Cancel</button>\''
        '+\'</div></div>\';'
        'var popup=new maplibregl.Popup({className:"ts-map-popup",offset:18,closeButton:false})'
        '.setLngLat(lngLat).setHTML(html).addTo(map);'
        'setTimeout(function(){'
        'var sb=document.getElementById("ec-save");'
        'var cb=document.getElementById("ec-cancel");'
        'if(sb)sb.addEventListener("click",function(){'
        'popup.remove();_saveCoordinate(slug,parseFloat(lat),parseFloat(lon));});'
        'if(cb)cb.addEventListener("click",function(){'
        'popup.remove();if(_dragMarker){_dragMarker.remove();_dragMarker=null;}});'
        '},40);'
        '}\n'

        'function _saveCoordinate(slug,lat,lon){'
        '_setApiStatus("Saving "+slug+"...");'
        'fetch("/api/locations/"+slug+"/coordinates",{'
        'method:"PUT",'
        'headers:{"Content-Type":"application/json"},'
        'body:JSON.stringify({lat:lat,lon:lon})})'
        '.then(function(r){return r.json();})'
        '.then(function(data){'
        'if(data.ok){'
        '_pendingEdits[slug]={lat:lat,lon:lon};'
        '_updateUnsavedList();'
        '_setApiStatus("✓ Saved "+slug,"ok");'
        '_updateLocationInSource(slug,lat,lon);'
        'if(_dragMarker){_dragMarker.remove();_dragMarker=null;}'
        '}else{_setApiStatus("✗ "+( data.error||"unknown error"),"err");}'
        '})'
        '.catch(function(){_setApiStatus("✗ Network error — devserver running?","err");});'
        '}\n'

        'function _updateLocationInSource(slug,lat,lon){'
        'var src=map.getSource("locations");'
        'if(!src)return;'
        'var gj=JSON.parse(JSON.stringify(_locGJ));'
        'gj.features.forEach(function(f){'
        'if((f.properties._slug||f.properties.slug)===slug){'
        'f.geometry.coordinates=[lon,lat];}});'
        'src.setData(gj);'
        '}\n'

        'function _updateUnsavedList(){'
        'var allSlugs=[...new Set([...Object.keys(_pendingEdits),...Object.keys(_pendingFieldEdits||{})])];'
        'var count=allSlugs.length;'
        'if(count===0){_editBadge.classList.add("hidden");_unsavedSection.classList.add("hidden");return;}'
        '_editBadge.textContent=count;_editBadge.classList.remove("hidden");'
        '_unsavedSection.classList.remove("hidden");'
        '_unsavedList.innerHTML=allSlugs.map(function(s){'
        'var parts=[];'
        'if(_pendingEdits[s]){var e=_pendingEdits[s];parts.push(e.lat.toFixed(5)+", "+e.lon.toFixed(5));}'
        'if(_pendingFieldEdits&&_pendingFieldEdits[s])parts.push("fields");'
        'return\'<li class="unsaved-item"><span class="ui-slug">\'+s+\'</span><span class="ui-coords">\'+parts.join(" · ")+\'</span></li>\';'
        '}).join("");'
        '}\n'

        'function _apiRebuild(target,btn){'
        'btn.disabled=true;'
        '_setApiStatus("Rebuilding "+target+"...");'
        'fetch("/api/rebuild/"+target,{method:"POST"})'
        '.then(function(r){return r.json();})'
        '.then(function(data){'
        'btn.disabled=false;'
        '_setApiStatus(data.ok?"✓ Rebuilt "+target:"✗ Rebuild failed — see devserver log",data.ok?"ok":"err");'
        '})'
        '.catch(function(){btn.disabled=false;_setApiStatus("✗ Network error","err");});'
        '}\n'

        '_rebuildLocBtn.addEventListener("click",function(){_apiRebuild("locations",_rebuildLocBtn);});\n'
        '_rebuildWsBtn.addEventListener("click",function(){_apiRebuild("workshop",_rebuildWsBtn);});\n'

        # -- Field editor (Phase 1+2+visibility) --
        'var _efSlug=null;\n'
        'var _efCurrentCoords=null;\n'
        'var _pendingFieldEdits={};\n'
        'var _efPanel=document.getElementById("ef-panel");\n'
        'var _efSlugEl=document.getElementById("ef-slug");\n'
        'var _efName=document.getElementById("ef-name");\n'
        'var _efFantasy=document.getElementById("ef-fantasy");\n'
        'var _efType=document.getElementById("ef-type");\n'
        'var _efMarker=document.getElementById("ef-marker");\n'
        'var _efStatus=document.getElementById("ef-status");\n'
        'var _efSaveBtn=document.getElementById("ef-save-btn");\n'
        'var _efMoveBtn=document.getElementById("ef-move-btn");\n'

        'function _openFieldEditor(feature){'
        'var p=feature.properties;'
        '_efSlug=p.slug||p._slug||"";'
        '_efCurrentCoords={lng:feature.geometry.coordinates[0],lat:feature.geometry.coordinates[1]};'
        '_efSlugEl.textContent=_efSlug;'
        '_efName.value=p.title||"";'
        'var fn=p.fantasyName||(p.label!==p.title?p.label:"");'
        '_efFantasy.value=(fn&&fn!==p.title)?fn:"";'
        'if(_efType.querySelector(\'option[value="\'+p.category+\'"]\'))_efType.value=p.category;'
        'var mm=p.mapMarker;'
        'var mmVal=mm===false?"false":(mm||"");'
        'if(_efMarker.querySelector(\'option[value="\'+mmVal+\'"]\'))_efMarker.value=mmVal;'
        'else _efMarker.value="";'
        'var visVal=p.visibility==="gm_secrets"?"gm_secrets":"public";'
        'document.querySelectorAll(\'input[name="ef-vis"]\').forEach(function(r){r.checked=r.value===visVal;});'
        '_efStatus.textContent="";_efStatus.className="hint";'
        '_efPanel.classList.remove("hidden");'
        '}\n'

        # Promise-returning PATCH shared by the field editor and the Reveal tab.
        # Resolves with the server's JSON; rejects only on a network failure.
        'function _patchFrontmatterRaw(slug,fields){'
        'return fetch("/api/locations/"+slug+"/frontmatter",{'
        'method:"PATCH",'
        'headers:{"Content-Type":"application/json"},'
        'body:JSON.stringify(fields)})'
        '.then(function(r){return r.json();})'
        '.then(function(data){'
        'if(data.ok){'
        '_pendingFieldEdits[slug]=Object.assign(_pendingFieldEdits[slug]||{},fields);'
        '_updateUnsavedList();'
        'if(fields.visibility)_syncVisibility(slug,fields.visibility);'
        '}'
        'return data;});'
        '}\n'

        # Keep the in-page copies of a location's visibility in step with the file
        'function _syncVisibility(slug,vis){'
        'if(_locBySlug[slug])_locBySlug[slug].visibility=vis;'
        '_locGJ.features.forEach(function(f){'
        'if((f.properties._slug||f.properties.slug)===slug)f.properties.visibility=vis;});'
        '}\n'
        'function _refreshLocSource(){'
        'var src=map.getSource("locations");'
        'if(src)src.setData(JSON.parse(JSON.stringify(_locGJ)));'
        '}\n'

        'function _patchFrontmatter(slug,fields){'
        '_efStatus.textContent="Saving…";_efStatus.className="hint";'
        '_patchFrontmatterRaw(slug,fields)'
        '.then(function(data){'
        'if(data.ok){'
        '_efStatus.textContent="✓ Saved";_efStatus.className="hint ok";'
        'if(fields.visibility)_refreshLocSource();'
        '}else{_efStatus.textContent="✗ "+(data.error||"error");_efStatus.className="hint err";}'
        '})'
        '.catch(function(){_efStatus.textContent="✗ Network error";_efStatus.className="hint err";});'
        '}\n'

        '_efSaveBtn.addEventListener("click",function(){'
        'if(!_efSlug)return;'
        'var mm=_efMarker.value;'
        'var vis=document.querySelector(\'input[name="ef-vis"]:checked\').value;'
        'var fields={'
        'name:_efName.value.trim(),'
        'fantasy_name:_efFantasy.value.trim()||null,'
        'type:_efType.value,'
        'mapmarker:mm==="false"?false:(mm||null),'
        'visibility:vis};'
        '_patchFrontmatter(_efSlug,fields);'
        '});\n'

        '_efMoveBtn.addEventListener("click",function(){'
        'if(!_efSlug||!_efCurrentCoords)return;'
        '_startDragEdit(_efSlug,_efCurrentCoords);'
        '});\n'

        # -- Reveal tab: staged earmarks, rings, Apply --
        + _REVEAL_JS +

        # -- Search / find-location widget --
        'var _wsSearch=document.getElementById("ws-search");'
        'var _wsSearchDrop=document.getElementById("ws-search-drop");'
        'var _wsSearchGroups=['
        '{lbl:"Major",cats:["city","capital","bridge","landmark","fortress"]},'
        '{lbl:"Towns",cats:["town"]},'
        '{lbl:"Sacred",cats:["sacred-site","power-site"]},'
        '{lbl:"Terrain",cats:["oasis","lake","water-body"]},'
        '{lbl:"Routes",cats:["route-node","caravanserai","chokepoint","mountain-pass"]},'
        '{lbl:"Other",cats:["ruins","poi","site","dungeon"]}'
        '];\n'

        'function _wsFlyTo(item){'
        'if(item&&item.lat!=null&&item.lon!=null){'
        'map.flyTo({center:[item.lon,item.lat],zoom:Math.max(map.getZoom(),8),duration:600});}'
        '_wsSearchDrop.hidden=true;_wsSearch.blur();}\n'

        'function _wsRender(q){'
        'q=(q||"").trim().toLowerCase();'
        'var html="",total=0;'
        '_wsSearchGroups.forEach(function(g){'
        'var items=_locList.filter(function(l){'
        'if(g.cats.indexOf(l.category)===-1)return false;'
        'if(!q)return true;'
        'return(l.label||"").toLowerCase().indexOf(q)!==-1||(l.title||"").toLowerCase().indexOf(q)!==-1;});'
        'if(!items.length)return;'
        'html+=\'<div class="wsd-group">\'+g.lbl+\'</div>\';'
        'items.forEach(function(itm){'
        'html+=\'<div class="wsd-item" data-slug="\'+itm.slug+\'">\'+'
        '(itm.label||itm.title)+\'</div>\';});'
        'total+=items.length;});'
        'var grouped=_wsSearchGroups.reduce(function(a,g){return a.concat(g.cats);},[]);'
        'var extra=_locList.filter(function(l){'
        'if(grouped.indexOf(l.category)!==-1)return false;'
        'if(!q)return true;'
        'return(l.label||"").toLowerCase().indexOf(q)!==-1||(l.title||"").toLowerCase().indexOf(q)!==-1;});'
        'if(extra.length){'
        'html+=\'<div class="wsd-group">Other</div>\';'
        'extra.forEach(function(itm){html+=\'<div class="wsd-item" data-slug="\'+itm.slug+\'">\'+'
        '(itm.label||itm.title)+\'</div>\';});'
        'total+=extra.length;}'
        'if(!total&&q)html=\'<div class="wsd-empty">No results for &ldquo;\'+q+\'&rdquo;</div>\';'
        '_wsSearchDrop.innerHTML=html;'
        '_wsSearchDrop.querySelectorAll(".wsd-item").forEach(function(el){'
        'el.addEventListener("click",function(){'
        '_wsFlyTo(_locBySlug[el.dataset.slug]);});});}\n'

        'if(_wsSearch){'
        '_wsSearch.addEventListener("focus",function(){_wsRender(_wsSearch.value);_wsSearchDrop.hidden=false;});'
        '_wsSearch.addEventListener("input",function(){_wsRender(_wsSearch.value);_wsSearchDrop.hidden=false;});'
        'document.addEventListener("click",function(e){'
        'if(!_wsSearchDrop.hidden&&!_wsSearchDrop.contains(e.target)&&e.target!==_wsSearch){'
        '_wsSearchDrop.hidden=true;}});}\n'

        # -- Travel tab: per-leg mode/path, saved journeys --
        + _TRAVEL_JS +

        # GM position broadcast (debounced moveend → POST /api/map-center)
        'var _mapCenterTimer=null;\n'
        'map.on("moveend",function(){'
        'clearTimeout(_mapCenterTimer);'
        '_mapCenterTimer=setTimeout(function(){'
        'var c=map.getCenter();'
        'fetch("/api/map-center",{method:"POST",'
        'headers:{"Content-Type":"application/json"},'
        'body:JSON.stringify({lng:c.lng,lat:c.lat,zoom:map.getZoom()})})'
        '.catch(function(){});},400);});\n'

        # Player share bar — populate from health check
        '(function(){'
        'var _shareBar=document.getElementById("player-share");'
        'var _shareLink=document.getElementById("player-share-link");'
        'var _shareCopy=document.getElementById("player-share-copy");'
        'if(!_shareBar)return;'
        'fetch("/api/health").then(function(r){return r.json();})'
        '.then(function(d){'
        'if(d.player_url){'
        '_shareLink.textContent=d.player_url;'
        '_shareLink.href=d.player_url;'
        '_shareBar.style.display="flex";'
        'if(_shareCopy)_shareCopy.addEventListener("click",function(){'
        'navigator.clipboard.writeText(d.player_url).then(function(){'
        'var t=_shareCopy.textContent;_shareCopy.textContent="Copied!";'
        'setTimeout(function(){_shareCopy.textContent=t;},1200);'
        '});});}}).catch(function(){});'
        '})();\n'
    )
    # fmt: on


TERRAIN_WORKER_PATH = Path(__file__).resolve().parent / "terrain_path.js"


def _terrain_worker_literal() -> str:
    """terrain_path.js as a JS string literal that is safe inside a <script> tag.

    The Workshop builds the Web Worker from this source via a Blob URL, so the
    page stays a single file with no worker asset to serve.
    """
    src = TERRAIN_WORKER_PATH.read_text(encoding="utf-8")
    return json.dumps(src).replace("</", "<\\/").replace("<!--", "<\\!--")


def _build_html(
    loc_geojson: dict,
    routes_geojson: dict,
    regions_geojson: dict,
    region_names: list,
    loc_list: list,
    route_index_html: str,
    maptiler_key: str,
    journeys_geojson: dict | None = None,
    journey_info: dict | None = None,
) -> str:
    journeys_geojson = journeys_geojson or {"type": "FeatureCollection", "features": []}
    journey_info = journey_info or {}
    style_url = (
        f"https://api.maptiler.com/maps/{MAPTILER_STYLE_ID}/style.json?key={maptiler_key}"
    )
    icons_js = icon_registration_js()

    data_js = (
        f"var _locGJ = {json.dumps(loc_geojson)};\n"
        f"var _routeGJ = {json.dumps(routes_geojson)};\n"
        f"var _TT = {travel_time.tt_json()};\n"
        f"var _TERRAIN_SRC = {_terrain_worker_literal()};\n"
        f"var _JRN = {journeys.config_json()};\n"
        f"var _journeyGJ = {json.dumps(journeys_geojson)};\n"
        f"var _jrnInfo = {json.dumps(journey_info)};\n"
        f"var _regionGJ = {json.dumps(regions_geojson)};\n"
        f"var _locList = {json.dumps(loc_list)};\n"
        f"var _regionList = {json.dumps(region_names)};\n"
    )

    cat_options = "\n".join(f'<option value="{c}">{c}</option>' for c in CATEGORIES)
    region_options = "\n".join(
        f'<option value="{r["slug"]}">{r["title"]}</option>' for r in region_names
    )
    mode_options = "".join(
        f'<option value="{m}">{spec["label"]} ({spec["kmpd"]} km/d)</option>'
        for m, spec in travel_time.SPEEDS.items()
    )

    panel_add = _build_panel_add_point(cat_options, region_options)
    panel_route = _build_panel_plan_route()
    panel_edit = _build_panel_edit_coords()
    panel_travel = _build_panel_travel_time()
    panel_reveal = _build_panel_reveal()
    app_js = _build_app_js(style_url, icons_js, maptiler_key=maptiler_key)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        "<title>Map Workshop — Tarim-Shaïal</title>\n"
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/maplibre-gl@5/dist/maplibre-gl.css">\n'
        "<style>\n" + _CSS + map_style.popup_css() + "</style>\n"
        "</head>\n"
        "<body>\n"
        '<div id="app">\n'
        '  <div id="sidebar">\n'
        '    <div id="ds-banner" hidden>\n'
        '      ⚠ Devserver not running — edits unavailable.\n'
        '      Run: <code>venv/bin/python utilities/devserver.py</code>\n'
        '      <button id="ds-banner-close" title="Dismiss">✕</button>\n'
        '    </div>\n'
        '    <div id="sidebar-header">\n'
        '      <div id="app-title">Map Workshop'
        '<a id="app-title-link" href="/world.html">← World</a>'
        '</div>\n'
        '      <div id="ws-subheader">\n'
        '        <button id="layers-btn">⊞ Layers</button>\n'
        '        <div id="layers-dropdown" hidden>\n'
        '          <label><input type="checkbox" id="topo-toggle"> Topo overlay\n'
        '            <input type="range" id="topo-opacity" min="0" max="100" value="55" title="Opacity"></label>\n'
        '          <label><input type="checkbox" id="sat-toggle"> Satellite Plain\n'
        '            <input type="range" id="sat-opacity" min="0" max="100" value="60" title="Opacity"></label>\n'
        '          <label><input type="checkbox" id="jrn-toggle" checked> Saved journeys</label>\n'
        '          <hr>\n'
        '          <div class="it-heading">Locations</div>\n'
        '          <div class="it-grid">\n'
        '            <label><input type="checkbox" class="it-cb" data-type="city" checked> Cities</label>\n'
        '            <label><input type="checkbox" class="it-cb" data-type="capital" checked> Capitals</label>\n'
        '            <label><input type="checkbox" class="it-cb" data-type="bridge" checked> Bridges</label>\n'
        '            <label><input type="checkbox" class="it-cb" data-type="landmark" checked> Landmarks</label>\n'
        '            <label><input type="checkbox" class="it-cb" data-type="fortress" checked> Fortresses</label>\n'
        '            <label><input type="checkbox" class="it-cb" data-type="town" checked> Towns</label>\n'
        '            <label><input type="checkbox" class="it-cb" data-type="sacred-site" checked> Sacred Sites</label>\n'
        '            <label><input type="checkbox" class="it-cb" data-type="oasis" checked> Oases</label>\n'
        '            <label><input type="checkbox" class="it-cb" data-type="lake" checked> Lakes</label>\n'
        '            <label><input type="checkbox" class="it-cb" data-type="route-node" checked> Route Nodes</label>\n'
        '            <label><input type="checkbox" class="it-cb" data-type="poi" checked> POIs</label>\n'
        '          </div>\n'
        '        </div>\n'
        '        <span id="ws-zoom">zoom <span id="ws-zoom-val">—</span></span>\n'
        '        <span id="ws-edit-dot" class="hidden">● Edit</span>\n'
        '      </div>\n'
        '      <div id="tab-bar">\n'
        '        <button class="tab-btn active" data-tab="add-point">Add Point</button>\n'
        '        <button class="tab-btn" data-tab="plan-route">Plan Route</button>\n'
        '        <button class="tab-btn" data-tab="route-index">Route Index</button>\n'
        '        <button class="tab-btn" data-tab="edit-coords">Edit Coords <span class="edit-badge hidden" id="edit-badge">0</span></button>\n'
        '        <button class="tab-btn" data-tab="travel-time">Travel Time</button>\n'
        '        <button class="tab-btn" data-tab="reveal">Reveal <span class="edit-badge hidden" id="rv-badge">0</span></button>\n'
        "      </div>\n"
        "    </div>\n"
        '    <div id="ws-search-row">\n'
        '      <div id="ws-search-wrap">\n'
        '        <span id="ws-search-icon">⌕</span>\n'
        '        <input id="ws-search" type="text" placeholder="Find location…" autocomplete="off" spellcheck="false">\n'
        '        <div id="ws-search-drop" hidden></div>\n'
        '      </div>\n'
        '    </div>\n'
        '    <div id="panel-add-point" class="panel active">\n'
        + panel_add
        + "\n    </div>\n"
        '    <div id="panel-plan-route" class="panel">\n'
        + panel_route
        + "\n    </div>\n"
        '    <div id="panel-route-index" class="panel">\n'
        + route_index_html
        + "\n    </div>\n"
        '    <div id="panel-edit-coords" class="panel">\n'
        + panel_edit
        + "\n    </div>\n"
        '    <div id="panel-travel-time" class="panel">\n'
        + panel_travel
        + "\n    </div>\n"
        '    <div id="panel-reveal" class="panel">\n'
        + panel_reveal
        + "\n    </div>\n"
        '    <div id="player-share" style="display:none">\n'
        '      <span style="color:#8ad08a;font-size:11px;white-space:nowrap;">📡 Players:</span>\n'
        '      <a id="player-share-link" href="#" target="_blank" style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"></a>\n'
        '      <button id="player-share-copy" title="Copy link">⎘</button>\n'
        '    </div>\n'
        "  </div>\n"
        '  <div id="map"></div>\n'
        '  <div id="route-panel" hidden>\n'
        '    <div id="route-panel-label"></div>\n'
        '    <div id="route-panel-time"></div>\n'
        '    <div id="route-panel-seen"></div>\n'
        '    <div class="rp-row"><label for="route-panel-vis">Visibility</label>'
        '<select id="route-panel-vis"><option value="gm_secrets">GM only</option>'
        '<option value="public">Public</option></select></div>\n'
        f'    <div class="rp-row"><label for="route-panel-mode">Travel by</label>'
        f'<select id="route-panel-mode">{mode_options}</select></div>\n'
        '    <button id="route-panel-regenerate">🔄 Regenerate</button>\n'
        '    <button id="route-panel-delete">🗑 Delete Route</button>\n'
        '    <button id="route-panel-close">✕</button>\n'
        '  </div>\n'
        "</div>\n"
        '<script src="https://cdn.jsdelivr.net/npm/maplibre-gl@5/dist/maplibre-gl.js"></script>\n'
        "<script>\n"
        + data_js
        + app_js
        + "\n</script>\n"
        "</body>\n"
        "</html>\n"
    )


# ---------------------------------------------------------------------------
# Player map HTML (public locations only, mobile-first, follows GM position)
# ---------------------------------------------------------------------------

def _build_player_html(
    loc_geojson: dict,
    routes_geojson: dict,
    maptiler_key: str,
    journeys_geojson: dict | None = None,
    journey_info: dict | None = None,
) -> str:
    journeys_geojson = journeys_geojson or {"type": "FeatureCollection", "features": []}
    journey_info = journey_info or {}
    style_url = (
        f"https://api.maptiler.com/maps/{MAPTILER_STYLE_ID}/style.json?key={maptiler_key}"
    )
    icons_js = icon_registration_js()
    data_js = (
        f"var _locGJ = {json.dumps(loc_geojson)};\n"
        f"var _routeGJ = {json.dumps(routes_geojson)};\n"
        f"var _journeyGJ = {json.dumps(journeys_geojson)};\n"
        f"var _jrnInfo = {json.dumps(journey_info)};\n"
    )

    proxy_style_path = f"/api/maptiler-proxy?url={urllib.parse.quote(style_url, safe='')}"

    app_js = (
        "var _following = true;\n"
        "var _pollTimer = null;\n"
        "var _lastCenter = null;\n"
        # Use location.origin so that transformRequest returns absolute URLs.
        # MapLibre fetches vector tiles in a blob:-URL Worker; relative URLs cannot
        # be resolved in that context and silently fail, leaving all vector tile
        # sources (water, rivers, land colour) empty.
        "var _proxyBase=window.location.origin;\n"

        f"var map = new maplibregl.Map({{"
        f"container:'map',"
        f"style:_proxyBase+'{proxy_style_path}',"
        f"center:[70,40],zoom:4,"
        f"transformRequest:function(url,resourceType){{"
        f"if(url.indexOf('https://api.maptiler.com/')===0){{"
        f"return{{url:_proxyBase+'/api/maptiler-proxy?url='+encodeURIComponent(url)}};}}"
        f"}}"
        f"}});\n"

        "map.addControl(new maplibregl.NavigationControl(), 'top-right');\n"
        "map.addControl(new maplibregl.ScaleControl({maxWidth:100,unit:'metric'}), 'bottom-right');\n"

        "map.on('load', function() {\n"
        + icons_js
        + "\n"
        "  map.addSource('locations', {type:'geojson', data: _locGJ});\n"
        + map_style.location_tiers_js()
        + "\n"
        "  map.addSource('routes', {type:'geojson', data: _routeGJ});\n"
        + map_style.routes_layer_js()
        + "\n"
        "  map.addSource('journeys', {type:'geojson', data: _journeyGJ});\n"
        + map_style.journeys_layer_js()
        + "\n"
        + map_style.hover_popup_js(gm_badge=False, tap_to_open=True)
        + "\n"
        + map_style.journey_hover_js(tap_to_open=True)
        + "\n"
        "  _startPolling();\n"
        "});\n"

        "function _startPolling(){\n"
        "  if(_pollTimer)return;\n"
        "  _pollTimer = setInterval(function(){\n"
        "    if(!_following)return;\n"
        "    fetch('/api/map-center').then(function(r){return r.json();})\n"
        "    .then(function(d){\n"
        "      if(d.lng==null||d.lat==null)return;\n"
        "      var key=d.lng.toFixed(5)+','+d.lat.toFixed(5)+(d.zoom!=null?','+d.zoom.toFixed(2):'');\n"
        "      if(key===_lastCenter)return;\n"
        "      _lastCenter=key;\n"
        "      var easeOpts={center:[d.lng,d.lat],duration:400};\n"
        "      if(d.zoom!=null)easeOpts.zoom=d.zoom;\n"
        "      map.easeTo(easeOpts);\n"
        "    }).catch(function(){});\n"
        "  },2000);\n"
        "}\n"

        "document.getElementById('follow-btn').addEventListener('click',function(){\n"
        "  _following=!_following;\n"
        "  this.textContent=_following?'● Following GM':'○ Follow GM';\n"
        "  this.classList.toggle('off',!_following);\n"
        "});\n"
    )

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta name="apple-mobile-web-app-capable" content="yes">\n'
        '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">\n'
        "<title>Tarim-Shaïal — Player Map</title>\n"
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/maplibre-gl@5/dist/maplibre-gl.css">\n'
        "<style>\n"
        "* { box-sizing: border-box; margin: 0; padding: 0; }\n"
        "html, body { width: 100%; height: 100%; overflow: hidden; background: #1a1208; }\n"
        "#map { position: fixed; inset: 0; width: 100%; height: 100%; }\n"
        "#follow-btn {\n"
        "  position: fixed;\n"
        "  bottom: calc(24px + env(safe-area-inset-bottom));\n"
        "  left: 50%; transform: translateX(-50%);\n"
        "  z-index: 100;\n"
        "  background: rgba(26,18,8,0.85);\n"
        "  color: #8ad08a;\n"
        "  border: 1px solid rgba(138,208,138,0.4);\n"
        "  border-radius: 20px;\n"
        "  padding: 10px 20px;\n"
        "  font-size: 14px;\n"
        "  font-family: Georgia, serif;\n"
        "  min-height: 44px;\n"
        "  cursor: pointer;\n"
        "  backdrop-filter: blur(6px);\n"
        "  touch-action: manipulation;\n"
        "  white-space: nowrap;\n"
        "}\n"
        "#follow-btn.off { color: #7a6a50; border-color: rgba(122,106,80,0.3); }\n"
        ".maplibregl-ctrl-bottom-right { bottom: calc(60px + env(safe-area-inset-bottom)) !important; }\n"
        + map_style.popup_css()
        + "</style>\n"
        "</head>\n"
        "<body>\n"
        '<div id="map"></div>\n'
        '<button id="follow-btn">● Following GM</button>\n'
        '<script src="https://cdn.jsdelivr.net/npm/maplibre-gl@5/dist/maplibre-gl.js"></script>\n'
        "<script>\n"
        + data_js
        + app_js
        + "\n</script>\n"
        "</body>\n"
        "</html>\n"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not MAPTILER_KEY:
        print("ERROR: MAPTILER_KEY environment variable is not set.", file=sys.stderr)
        print("  Export it in your shell or add it to .env at vault root.", file=sys.stderr)
        return 1

    for warning in map_style.check_tier_coverage():
        print(f"  WARN: {warning}", file=sys.stderr)

    print("  Loading locations...")
    locations = load_all_locations(LOCATIONS_DIR)
    loc_geojson = _build_locations_geojson(locations)
    n_with_coords = len(loc_geojson["features"])
    print(f"  {len(locations)} locations loaded, {n_with_coords} with coordinates")

    loc_list = sorted(
        [
            {
                "slug": loc["slug"],
                "title": loc["title"],
                "label": loc["fantasy_name"] or loc["title"],
                "lat": loc["lat"],
                "lon": loc["lon"],
                "region": loc["parent_region"] or "",
                "category": loc["location_type"] or "",
                "mapMarker": loc["map_marker"],
                "mapLabel": loc["map_label"],
                "visibility": loc["visibility"],
            }
            for loc in locations
            if loc["lat"] is not None and loc["lon"] is not None
        ],
        key=lambda l: l["label"],
    )

    routes_geojson: dict = {"type": "FeatureCollection", "features": []}
    if ROUTES_PATH.exists():
        routes_geojson = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
        print(f"  {len(routes_geojson.get('features', []))} route features loaded")
    else:
        print("  WARN: routes GeoJSON not found", file=sys.stderr)

    regions_geojson: dict = {"type": "FeatureCollection", "features": []}
    region_names: list = []
    if REGIONS_PATH.exists():
        regions_geojson = json.loads(REGIONS_PATH.read_text(encoding="utf-8"))
        for f in regions_geojson.get("features", []):
            title = f.get("properties", {}).get("title", "")
            fid = f.get("id", "")
            slug = fid.replace("region_", "") if fid else ""
            if title:
                region_names.append({"slug": slug, "title": title})
        region_names.sort(key=lambda r: r["title"])
        print(f"  {len(region_names)} regions loaded")
    else:
        print("  WARN: regions GeoJSON not found", file=sys.stderr)

    # Workshop sees every route, flagged with whether players would; the player map
    # gets only the routes route_visibility lets through (matched against ALL locations).
    workshop_routes = annotate_routes(routes_geojson, loc_geojson)
    player_routes = route_visibility.visible_routes(routes_geojson, loc_geojson)
    route_index = _build_route_index(workshop_routes)
    ri_html = _route_index_html(route_index)

    # Journeys follow the same split: the Workshop gets every journey with its full
    # stops/legs (for editing) flagged _playerVisible; players get name + geometry of
    # the journeys journey_is_public lets through, judged against ALL locations.
    journeys_gj = journeys.load(JOURNEYS_PATH)
    workshop_journeys = journeys.annotate_player_visible(journeys_gj, loc_geojson)
    _, workshop_jrn_info = journeys.gm_payload(journeys_gj)
    player_jrn_gj, player_jrn_info = journeys.player_payload(journeys_gj, loc_geojson)

    html = _build_html(
        loc_geojson=loc_geojson,
        routes_geojson=workshop_routes,
        regions_geojson=regions_geojson,
        region_names=region_names,
        loc_list=loc_list,
        route_index_html=ri_html,
        maptiler_key=MAPTILER_KEY,
        journeys_geojson=workshop_journeys,
        journey_info=workshop_jrn_info,
    )

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"\n  Written: {OUTPUT_PATH.name}")

    # Player map — public locations only
    pub_geojson = _player_locations_geojson(loc_geojson)
    public_features = pub_geojson["features"]
    player_html = _build_player_html(
        loc_geojson=pub_geojson,
        routes_geojson=player_routes,
        maptiler_key=MAPTILER_KEY,
        journeys_geojson=player_jrn_gj,
        journey_info=player_jrn_info,
    )
    PLAYER_PATH.write_text(player_html, encoding="utf-8")
    print(f"  Written: {PLAYER_PATH.name}  ({len(public_features)} public locations, "
          f"{len(player_routes['features'])} of {len(routes_geojson.get('features', []))} routes, "
          f"{len(player_jrn_gj['features'])} of {len(journeys_gj['features'])} journeys)")
    print(f"  Run:     open {OUTPUT_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())


from shared.base_generator import make_generator
generator = make_generator(
    "workshop",
    "Map workshop HTML (requires MAPTILER_KEY; skipped in 'all' when key is absent)",
    main,
)
