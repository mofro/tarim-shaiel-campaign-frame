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

import html
import json
import math
import os
import sys
import urllib.parse
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent

sys.path.insert(0, str(SCRIPT_DIR.parent))

from locations.categories import CATEGORIES, type_icons
from locations.location_parser import load_all_locations
from locations.map_icons import ICON_NAMES, icon_registration_js
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


_EYE_OPEN = ('<svg class="ri-eye" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">'
             '<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" fill="none" stroke="currentColor" stroke-width="2"/>'
             '<circle cx="12" cy="12" r="3.2" fill="currentColor"/></svg>')
_EYE_SHUT = ('<svg class="ri-eye" viewBox="0 0 24 24" width="16" height="16" aria-hidden="true">'
             '<path d="M2 10c3 5 17 5 20 0M6 14.5l-2 3M12 16v3.5M18 14.5l2 3" fill="none" '
             'stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>')
_VIS_LABEL = {"pub": "Players see this route",
              "held": "Public, but an end location is hidden from players",
              "gm": "GM only"}


def _vis_icon(state: str) -> str:
    icon = _EYE_OPEN if state == "pub" else _EYE_SHUT
    return (f'<span class="ri-vis ri-vis-{state}" role="img" '
            f'aria-label="{_VIS_LABEL[state]}" title="{_VIS_LABEL[state]}">{icon}</span>')


def _route_index_html(route_index: list) -> str:
    main_routes = [r for r in route_index if r["kind"] == "main"]
    spurs = [r for r in route_index if r["kind"] == "spur"]

    def row(r: dict) -> str:
        p = "~" if r["is_approx"] else ""
        d = f'{p}{int(r["dist_km"])} km'
        mode = travel_time.SPEEDS[r["mode"]]["label"]
        if r["player_visible"]:
            vis = _vis_icon("pub")
        elif r["visibility"] == route_visibility.PUBLIC:
            vis = _vis_icon("held")
        else:
            vis = _vis_icon("gm")
        return (
            f'<tr class="ri-row" data-id="{r["id"]}" style="cursor:pointer">'
            f'<td class="ri-check"><input type="checkbox" class="ri-cb" data-id="{r["id"]}"></td>'
            f'<td class="ri-label" title="{html.escape(r["id"], quote=True)}">{html.escape(str(r["label"]))}</td>'
            f'<td>{d}</td>'
            f'<td>{r["time"]} <span class="ri-mode">{mode}</span></td>'
            f'<td>{vis}</td>'
            f'</tr>'
        )

    def section(title: str, rows: list) -> str:
        if not rows:
            return ""
        thead = ('<thead><tr><th class="ri-check"></th><th>Route</th>'
                 '<th>Dist.</th><th>Travel</th><th class="ri-vis-col" title="Visible to players">'
                 + _EYE_OPEN + '</th></tr></thead>')
        tbody = "<tbody>" + "".join(row(r) for r in rows) + "</tbody>"
        return f'<h3 data-collapsible>{title}</h3><table>{thead}{tbody}</table>'

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

# The sidebar sections, in order. One list renders both the tab strip and the icon rail,
# so the two navigations cannot drift (#355). Icons are 20px stroke SVGs on currentColor.
_WS_SECTIONS = [
    ("inspector", "Inspector",
     '<circle cx="10" cy="10" r="4.5"/><path d="M10 1.5v4M10 14.5v4M1.5 10h4M14.5 10h4"/>'),
    ("route-index", "Routes",
     '<circle cx="4.5" cy="15.5" r="2"/><circle cx="15.5" cy="4.5" r="2"/>'
     '<path d="M6.5 15.5c6 0 1.5-11 7-11"/>'),
    ("travel-time", "Journeys",
     '<path d="M3 16c3-8 6 0 9-6s3-5 5-6" stroke-dasharray="2.5 2.5"/><circle cx="17" cy="4" r="1.6"/>'),
]


def _tab_buttons_html() -> str:
    out = []
    for i, (sid, label, _svg) in enumerate(_WS_SECTIONS):
        badge = (' <span class="edit-badge hidden" id="edit-badge">0</span>'
                 if sid == "inspector" else "")
        out.append(f'        <button class="tab-btn{" active" if i == 0 else ""}" '
                   f'data-tab="{sid}">{label}{badge}</button>\n')
    out.append('        <button type="button" class="nav-switch" id="nav-to-rail" '
               'title="Switch to the icon rail" aria-label="Switch to the icon rail">\u25a5</button>\n')
    return "".join(out)


def _nav_rail_html() -> str:
    items = []
    for i, (sid, label, svg) in enumerate(_WS_SECTIONS):
        badge = ('<span class="edit-badge hidden" id="edit-badge-rail">0</span>'
                 if sid == "inspector" else "")
        cur = ' aria-current="page"' if i == 0 else ""
        items.append(
            f'<button type="button" class="nav-item{" active" if i == 0 else ""}" data-tab="{sid}" '
            f'title="{label}" aria-label="{label}"{cur}>'
            f'<svg class="nav-ico" viewBox="0 0 20 20" width="20" height="20" fill="none" '
            f'stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true">{svg}</svg>'
            f'<span class="nav-label">{label}</span>{badge}</button>')
    foot = (
        '<div class="nav-foot">'
        '<button type="button" class="nav-item" id="nav-pin" aria-pressed="false" '
        'title="Pin the rail open" aria-label="Pin the rail open">'
        '<span class="nav-ico nav-glyph" aria-hidden="true">\u25b8</span><span class="nav-label">Pin open</span></button>'
        '<button type="button" class="nav-item" id="nav-to-tabs" '
        'title="Switch to tabs" aria-label="Switch to tabs">'
        '<span class="nav-ico nav-glyph" aria-hidden="true">\u25a4</span><span class="nav-label">Use tabs</span></button>'
        '</div>')
    return ('    <nav id="nav-rail" aria-label="Workshop sections"><div id="nav-rail-inner">'
            + "".join(items) + foot + '</div></nav>\n')


_CSS = """\
:root {
  /* Type scale: 5 rem steps, each >= 1.15x the last. 12px is the floor for
     uppercase or tracked labels, 14px for lowercase text. */
  --fs-1: 0.75rem;
  --fs-2: 0.875rem;
  --fs-3: 1.0625rem;
  --fs-4: 1.25rem;
  --fs-5: 1.5rem;
  --sb-w: 384px;
  /* Text colours, all >= 4.5:1 on the darkest-to-lightest sidebar backgrounds */
  --ink: #e8dcc4;
  --ink-2: #c8b890;
  --muted: #9a8a6a;
  --warn: #e8a060;
  --danger: #e07a7a;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; overflow: hidden; font-family: 'Georgia', serif;
  background: #0a0805; color: #e8dcc4; }
#app { display: flex; height: 100vh; position: relative; }
#sidebar { width: var(--sb-w); min-width: 340px; max-width: 70vw; flex: none;
  display: flex; flex-direction: column;
  background: #120f08; border-right: 1px solid rgba(184,146,44,0.3); overflow: hidden; }
#sidebar-header { padding: 12px 14px 0; border-bottom: 1px solid rgba(184,146,44,0.2);
  flex-shrink: 0; }
#app-title { font-size: var(--fs-2); letter-spacing: 0.12em; text-transform: uppercase;
  color: #b8922c; margin-bottom: 6px; }
#tab-bar { display: flex; gap: 2px; }
.tab-btn { position: relative; flex: 1 1 auto; white-space: nowrap; padding: 8px 4px; font-size: var(--fs-1); letter-spacing: 0;
  text-transform: uppercase; background: #1a1410; border: 1px solid rgba(184,146,44,0.2);
  border-bottom: none; color: var(--muted); cursor: pointer; border-radius: 3px 3px 0 0;
  transition: background 0.15s; }
.edit-badge { position: absolute; top: -5px; right: -3px; background: #4a7a1c; color: #fff; font-size: var(--fs-1);
  border-radius: 8px; padding: 0 4px; line-height: 14px; }
.tab-btn:hover { background: #221c12; color: #c8a84a; }
.tab-btn.active { background: #0a0805; color: #e8dcc4; border-color: rgba(184,146,44,0.4);
  border-bottom-color: #0a0805; font-weight: bold; }
.panel { display: none; flex-direction: column; flex: 1; overflow-y: auto; scrollbar-gutter: stable;
  padding: 18px 16px 24px; gap: 22px; }
.panel.active { display: flex; }
#insp-single { display: flex; flex-direction: column; gap: 18px; }
.field-group { display: flex; flex-direction: column; gap: 8px; }
.field-group label { font-size: var(--fs-1); text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--muted); }
.field-group input[type="text"], .field-group select, .field-group textarea {
  background: #1a1410; border: 1px solid rgba(184,146,44,0.3); color: #e8dcc4;
  padding: 10px 12px; min-height: 40px; font-size: var(--fs-2); border-radius: 3px; font-family: inherit; }
.field-group input[type="text"]:focus, .field-group select:focus, .field-group textarea:focus {
  outline: none; border-color: rgba(184,146,44,0.7); }
.field-group select option { background: #1a1410; }
.field-group textarea { resize: vertical; min-height: 56px; }
.insp-head { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.insp-head .list-heading { margin: 0; min-width: 0; overflow-wrap: anywhere; font-size: var(--fs-4);
  letter-spacing: 0.02em; text-transform: none; color: #e8dcc4; }
.insp-slug { color: var(--muted); font-size: var(--fs-2); text-transform: none; letter-spacing: 0; }
.insp-note { color: var(--muted); font-size: var(--fs-1); text-transform: none; letter-spacing: 0; }
.insp-actions { margin-top: 2px; }
.insp-status { min-height: 1.2em; }
.ef-adv { border-top: 1px solid rgba(184,146,44,0.25); padding-top: 16px; margin-top: 4px; }
.ef-adv summary { cursor: pointer; font-size: var(--fs-2); color: #c8a84a; padding: 4px 0; }
.ef-adv .field-group, .ef-adv .adv-ro { margin-top: 18px; }
.adv-check { display: flex; align-items: center; gap: 6px; cursor: pointer; }
.adv-ro-key { font-size: var(--fs-1); text-transform: uppercase; letter-spacing: 0.07em; color: var(--muted); }
.adv-ro pre { margin: 4px 0 0; padding: 6px 8px; background: #120e08; color: #b9ad94;
  font-size: var(--fs-2); white-space: pre-wrap; overflow-wrap: anywhere; border-radius: 2px; }
.coord-row { display: flex; gap: 10px; align-items: center; font-size: var(--fs-2); }
.coord-row span { color: var(--muted); font-size: var(--fs-2); }
.coord-row input { flex: 1; min-width: 0; }
.coord-row .btn { flex: none; white-space: nowrap; }
.radio-row { display: flex; gap: 22px; padding: 2px 0; font-size: var(--fs-2); }
.radio-row label { display: flex; align-items: center; gap: 8px; cursor: pointer; padding: 4px 0; }
.radio-row input[type="radio"] { accent-color: #b8922c; }
.btn { padding: 10px 16px; min-height: 40px; background: #2a1e08; border: 1px solid rgba(184,146,44,0.5);
  color: #e8dcc4; font-size: var(--fs-2); cursor: pointer; border-radius: 2px;
  letter-spacing: 0.05em; transition: background 0.15s; }
.btn:hover:not(:disabled) { background: #3a2a10; border-color: #b8922c; }
.btn:disabled { opacity: 0.4; cursor: default; }
.btn-sm { padding: 8px 14px; min-height: 36px; font-size: var(--fs-2); }
.btn-danger { border-color: rgba(180, 60, 60, 0.5); }
.btn-danger:hover:not(:disabled) { background: #3a1010; border-color: var(--danger); }
.btn-row { display: flex; flex-wrap: wrap; gap: 12px; }
.command-block { background: #0d0a06; border: 1px solid rgba(184,146,44,0.3);
  border-radius: 2px; overflow: hidden; }
.command-block pre { padding: 10px 12px; font-size: var(--fs-2); font-family: monospace;
  white-space: pre-wrap; word-break: break-all; color: #c8b890; line-height: 1.5; }
.command-block .btn { border-radius: 0; border: none; border-top: 1px solid rgba(184,146,44,0.2);
  width: 100%; text-align: center; }
.hint { font-size: var(--fs-2); color: var(--muted); line-height: 1.5; }
.ef-icon-note { font-size: var(--fs-2); color: #c8b890; line-height: 1.4; min-height: 18px; }
.hint code { font-family: monospace; color: #9a8a60; background: rgba(255,255,255,0.04);
  padding: 1px 4px; border-radius: 2px; }
.hidden { display: none !important; }
/* Route queue */
#route-queue-list { list-style: none; display: flex; flex-direction: column; gap: 6px; }
.queue-item { background: #1a1410; border: 1px solid rgba(184,146,44,0.2);
  border-radius: 2px; padding: 9px 12px; font-size: var(--fs-2); }
.queue-item .qi-num { color: #b8922c; font-weight: bold; margin-right: 6px; }
.queue-item .qi-label { color: #e8dcc4; }
.queue-item .qi-dist { color: var(--muted); font-size: var(--fs-2); margin-top: 2px; }
.queue-empty { color: var(--muted); font-size: var(--fs-2); font-style: italic; }
/* Route index */
.panel#panel-route-index { gap: 20px; }
#panel-route-index h3 { font-size: var(--fs-1); text-transform: uppercase;
  letter-spacing: 0.1em; color: #b8922c; margin-top: 10px; padding-top: 18px;
  border-top: 1px solid rgba(184,146,44,0.25); }
#panel-route-index h3:first-child { margin-top: 0; padding-top: 0; border-top: 0; }
#panel-route-index table { width: 100%; table-layout: fixed; border-collapse: collapse; font-size: var(--fs-2); }
#panel-route-index th:nth-child(1) { width: 28px; }
#panel-route-index th:nth-child(3) { width: 3.6rem; }
#panel-route-index th:nth-child(4) { width: 4.6rem; }
#panel-route-index th:nth-child(5) { width: 2rem; text-align: center; }
#panel-route-index td:nth-child(2) { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
#panel-route-index td { overflow-wrap: anywhere; }
#panel-route-index th { white-space: nowrap; }
#panel-route-index th { color: var(--muted); text-align: left; padding: 4px 6px;
  border-bottom: 1px solid rgba(184,146,44,0.2); }
#panel-route-index td { padding: 4px 6px; border-bottom: 1px solid rgba(255,255,255,0.04); }
.ri-note { font-size: var(--fs-2); color: var(--muted); margin-top: 4px; }
.ri-row:hover td { background: rgba(184,146,44,0.07); }
.ri-row.active td { background: rgba(184,146,44,0.14); }
/* Route section separator */
.route-or { text-align: center; color: var(--muted); font-size: var(--fs-2); margin: 4px 0; }
/* Route index delete controls */
.ri-header { display:flex; align-items:center; gap:8px; padding:4px 0 8px; }
.ri-select-all-label { font-size: var(--fs-2); color:var(--muted); display:flex; align-items:center; gap:5px; cursor:pointer; }
.ri-select-all-label input { accent-color:#b8922c; }
#ri-delete-btn { padding:4px 10px; font-size: var(--fs-2); background:#2a0e08;
  border:1px solid rgba(180,60,60,0.5); color:#e8a090; cursor:pointer; border-radius:2px; }
#ri-delete-btn:hover { background:#3a1010; border-color:var(--danger); }
.ri-check { width:28px; text-align:center; }
.ri-check input[type=checkbox] { accent-color:#b8922c; cursor:pointer; }
.ri-mode { color:var(--muted); font-size: var(--fs-2); }
.ri-vis { display: inline-flex; align-items: center; justify-content: center; }
.ri-vis-pub { color:#9bc47a; }
.ri-vis-held { color:#d9a441; }
.ri-vis-gm { color:var(--muted); }
.ri-vis-col { color: var(--muted); text-align: center; }
.ri-eye { display: block; }
/* Route form, docked in the Inspector (replaces the old map overlay) */
#route-panel { display:flex; flex-direction:column; gap:22px; font-size: var(--fs-2); }
#route-panel[hidden] { display:none; }
body.rt-selected #insp-single { display:none; }
#route-panel .rp-head { display:flex; align-items:flex-start; gap:8px; }
#route-panel .rp-title { flex:1; min-width:0; margin:0; font-size:var(--fs-4); letter-spacing:0.02em;
  color:#e8dcc4; overflow-wrap:anywhere; font-weight:normal; }
#route-panel-label { color:var(--muted); font-size:var(--fs-2); overflow-wrap:anywhere; }
#route-panel .rp-row { display:flex; align-items:center; gap:12px; }
#route-panel .rp-row label { font-size: var(--fs-2); color:var(--muted); min-width:72px; }
#route-panel .rp-row select { flex:1; background-color:#1a1408; color:#e8dcc4;
  border:1px solid rgba(184,146,44,0.35); padding:9px 10px; min-height:40px; font-size: var(--fs-2); border-radius:3px; }
#route-panel-time { font-size: var(--fs-2); color:#c8b98a; }
#route-panel-seen { font-size: var(--fs-2); color:var(--muted); }
#route-panel-seen.rp-yes { color:#9bc47a; }
#route-panel-seen.rp-held { color:#d9a441; }
/* The one close control for every edit form */
.close-x { flex:none; width:34px; height:34px; display:flex; align-items:center; justify-content:center;
  background:none; color:#b8922c; border:1px solid rgba(184,146,44,0.5); border-radius:3px;
  cursor:pointer; font-size: var(--fs-2); line-height:1; }
.close-x:hover { border-color:#b8922c; color:#e8dcc4; background:#2a1e08; }
.close-x.hidden { display:none; }
/* Edit forms read as one family of cards, apart from the tab bar and persistent controls */
#insp-single, #route-panel { background:#120e08; border:1px solid rgba(184,146,44,0.3);
  border-radius:4px; padding:16px; }
/* Native selects pin the arrow to the border; draw our own, inset */
.panel select { -webkit-appearance:none; appearance:none; padding-right:36px;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8'%3E%3Cpath d='M1 1.5l5 5 5-5' fill='none' stroke='%23b8922c' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E");
  background-repeat:no-repeat; background-position:right 14px center; background-size:12px 8px; }
.tt-leg-row select { padding-right:26px; background-position:right 8px center; }
/* Map */
#map { flex: 1; }
.maplibregl-map { font: inherit; }
/* Edit Coords panel */
.list-heading { font-size: var(--fs-1); text-transform: uppercase; letter-spacing: 0.07em;
  color: var(--muted); margin-bottom: 6px; margin-top: 8px; }
/* Devserver banner */
#ds-banner { display:flex; align-items:center; gap:8px; padding:5px 14px;
  background:#3a1a00; border-bottom:1px solid rgba(220,100,30,0.5);
  font-size: var(--fs-2); color:var(--warn); flex-shrink:0; }
#ds-banner[hidden] { display:none; }
#ds-banner code { font-family:monospace; background:rgba(255,255,255,0.08);
  padding:1px 5px; border-radius:2px; color:#f0c090; }
#ds-banner-close { margin-left:auto; background:none; border:none; color:var(--warn);
  cursor:pointer; font-size: var(--fs-2); line-height:1; padding:0 2px; }
/* Subheader toolbar */
#ws-subheader { display:flex; align-items:center; gap:8px; padding:5px 0 6px;
  border-bottom:1px solid rgba(184,146,44,0.15); position:relative; margin-bottom:6px; }
#layers-btn { background:none; border:1px solid rgba(184,146,44,0.4); color:#c8a84a;
  padding:3px 9px; border-radius:3px; font-size: var(--fs-1); cursor:pointer;
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
#ws-zoom { margin-left:auto; color:var(--muted); font-size: var(--fs-2); letter-spacing:0.06em; }
#ws-zoom-val { color:#c8a84a; font-weight:bold; }
#layers-dropdown label.ov-share { margin-top:2px; padding-left:22px; font-size: var(--fs-2);
  text-transform:none; letter-spacing:0; color:var(--muted); }
#preview-toggle,#topo-share,#sat-share { accent-color:#b8922c; cursor:pointer; }
.overlay-err { display:inline-flex; align-items:center; background:#7a1f00; color:#ffcc88;
  font-size: var(--fs-1); padding:1px 4px; border-radius:3px; cursor:help; margin-left:2px; vertical-align:middle; }
#unsaved-list { list-style: none; display: flex; flex-direction: column; gap: 3px;
  max-height: 140px; overflow-y: auto; }
.unsaved-item { font-size: var(--fs-2); padding: 5px 8px; background: #1a1410;
  border: 1px solid rgba(184,146,44,0.15); border-radius: 2px; }
.ui-slug { font-family: monospace; color: #e8dcc4; }
.ui-coords { color: var(--muted); margin-left: 6px; }
.rebuild-section { margin-top: 8px; }
#api-status { min-height: 16px; color: var(--muted); }
#api-status.ok { color: #6a9a2c; }
#api-status.err { color: var(--danger); }
/* Batch bar (multi-select visibility) */
#ms-list, #ms-confirm-list { list-style: none; display: flex; flex-direction: column; gap: 4px; }
#ms-list { max-height: 240px; overflow-y: auto; }
.ms-item { display: flex; align-items: flex-start; justify-content: space-between; gap: 8px; }
.ms-main { flex: 1; min-width: 0; }
.ms-x, .ms-name { background: none; border: none; cursor: pointer; font-family: inherit; }
.ms-x { color: var(--muted); font-size: var(--fs-2); padding: 0 2px; }
.ms-x:hover { color: #e8dcc4; }
.ms-name { color: #e8dcc4; font-size: var(--fs-2); padding: 0; text-align: left; }
.ms-name:hover { color: #f5d060; }
.ms-vis { color: var(--muted); font-size: var(--fs-2); }
.ms-err { color: var(--danger); font-size: var(--fs-2); margin-top: 2px; }
#ms-confirm { border: 1px solid rgba(184,146,44,0.5); background: #1a1410;
  border-radius: 2px; padding: 8px 10px; }
#ms-confirm-list { font-size: var(--fs-2); color: #e8dcc4; max-height: 120px; overflow-y: auto;
  margin: 6px 0; padding-left: 14px; list-style: disc; }
#ms-status { min-height: 16px; color: var(--muted); }
#ms-status.ok { color: #6a9a2c; }
#ms-status.err { color: var(--danger); }
body.ms-multi #insp-single { display: none; }
.drag-edit-marker { width: 22px; height: 22px; background: #f5d060;
  border: 2.5px solid #2a1e08; border-radius: 50%; cursor: grab;
  box-shadow: 0 2px 10px rgba(0,0,0,0.6); }
.drag-edit-marker:active { cursor: grabbing; }
/* World link in header */
#app-title-link { font-size: var(--fs-2); text-transform: none; letter-spacing: 0.03em;
  color: var(--muted); text-decoration: none; float: right; margin-top: 2px; }
#app-title-link:hover { color: #b8922c; }
/* Nav rail: icon bar that expands to labels over the panels (#355) */
#sb-main { display: flex; flex: 1; min-height: 0; position: relative; }
#sb-panels { display: flex; flex-direction: column; flex: 1; min-width: 0; min-height: 0; }
#nav-rail { flex: none; width: 48px; position: relative; z-index: 4; }
#nav-rail-inner { position: absolute; top: 0; bottom: 0; left: 0; width: 48px; overflow: hidden;
  display: flex; flex-direction: column; background: #0e0b06;
  border-right: 1px solid rgba(184,146,44,0.25); transition: width 0.15s; }
#nav-rail:hover #nav-rail-inner, #nav-rail:focus-within #nav-rail-inner,
#nav-rail.open #nav-rail-inner { width: 176px; box-shadow: 6px 0 14px rgba(0,0,0,0.45); }
#app.nav-pinned #nav-rail { width: 176px; }
/* a pinned rail only reserves width when the sidebar is wide enough to spare it */
#app.nav-pinned.nav-narrow #nav-rail { width: 48px; }
#app.nav-pinned.nav-narrow #nav-rail-inner { box-shadow: 6px 0 14px rgba(0,0,0,0.45); }
#app.nav-pinned #nav-rail-inner, #app.nav-pinned #nav-rail:hover #nav-rail-inner { width: 176px; box-shadow: none; }
.nav-item { position: relative; display: flex; align-items: center; gap: 14px; flex: none;
  width: 100%; height: 46px; padding: 0 11px; background: none; border: 0;
  border-left: 3px solid transparent; color: var(--muted); cursor: pointer; white-space: nowrap;
  font: inherit; font-size: var(--fs-1); letter-spacing: 0.07em; text-transform: uppercase; text-align: left; }
.nav-item:hover { background: #1a1410; color: #c8a84a; }
.nav-item.active { background: #1a1410; color: var(--ink); border-left-color: #b8922c; }
.nav-item:focus-visible, .nav-switch:focus-visible { outline: 2px solid #b8922c; outline-offset: -2px; }
.nav-ico { flex: none; width: 20px; height: 20px; }
.nav-glyph { display: flex; align-items: center; justify-content: center; font-size: var(--fs-3); line-height: 1; }
.nav-label { opacity: 0; transition: opacity 0.1s; }
#nav-rail:hover .nav-label, #nav-rail:focus-within .nav-label, #nav-rail.open .nav-label,
#app.nav-pinned .nav-label { opacity: 1; }
.nav-item .edit-badge { top: 6px; left: 26px; right: auto; }
.nav-foot { margin-top: auto; border-top: 1px solid rgba(184,146,44,0.2); padding: 6px 0; }
#nav-pin[aria-pressed=true] { color: #e8dcc4; }
#nav-pin[aria-pressed=true] .nav-glyph { transform: rotate(180deg); }
.nav-switch { flex: none; padding: 8px 10px; background: #1a1410; color: var(--muted);
  border: 1px solid rgba(184,146,44,0.2); border-bottom: none; border-radius: 3px 3px 0 0; cursor: pointer;
  font-size: var(--fs-2); }
.nav-switch:hover { color: #c8a84a; background: #221c12; }
#app.nav-tabs #nav-rail { display: none; }
#app:not(.nav-tabs) #tab-bar { display: none; }
#app:not(.nav-tabs) #sidebar-header { padding-bottom: 12px; }
/* Shell: hide, resize, collapse */
#sb-toggle { float: right; margin: 0 10px 0 0; background: none; color: var(--muted);
  border: 1px solid rgba(184,146,44,0.3); border-radius: 2px; cursor: pointer;
  font-size: var(--fs-2); line-height: 1; padding: 2px 6px; }
#sb-toggle:hover { color: #e8dcc4; border-color: #b8922c; }
#ws-mode-chip { position: absolute; top: 10px; left: 50%; transform: translateX(-50%); z-index: 6;
  display: flex; align-items: center; gap: 10px; background: #120f08; color: #f5d060;
  border: 1px solid #b8922c; border-radius: 3px; padding: 6px 10px; font-size: var(--fs-2); }
#ws-mode-chip[hidden] { display: none; }
#ws-mode-cancel { background: none; color: #c8a84a; border: 1px solid rgba(184,146,44,0.5);
  border-radius: 2px; cursor: pointer; font-size: var(--fs-1); padding: 1px 6px; }
.arm-btn[aria-pressed=true] { background: rgba(184,146,44,0.35); color: #f5d060; border-color: #b8922c; }
body.mode-place #map .maplibregl-canvas, body.mode-route #map .maplibregl-canvas { cursor: crosshair; }
#sb-resizer { flex: none; width: 6px; margin-left: -3px; cursor: col-resize; z-index: 5;
  background: transparent; touch-action: none; }
#sb-resizer:hover, #sb-resizer.drag, #sb-resizer:focus-visible {
  background: rgba(184,146,44,0.45); outline: none; }
#sb-float { display: none; position: absolute; top: 10px; left: 10px; z-index: 6;
  align-items: center; gap: 8px; background: #120f08; border: 1px solid rgba(184,146,44,0.5);
  border-radius: 3px; padding: 6px 10px; }
#sb-float #ws-subheader { border-bottom: 0; margin: 0; padding: 0; }
#sb-show { background: none; color: #c8a84a; border: 0; cursor: pointer;
  font-size: var(--fs-2); padding: 0 8px 0 0; border-right: 1px solid rgba(184,146,44,0.3); }
#sb-show:hover { color: #e8dcc4; }
.info-btn { background: none; color: #c8a84a; border: 1px solid rgba(184,146,44,0.5);
  border-radius: 50%; width: 1.25rem; height: 1.25rem; line-height: 1; cursor: pointer;
  font-size: var(--fs-1); font-style: italic; font-family: serif; padding: 0; vertical-align: middle; }
.info-btn:hover, .info-btn[aria-expanded=true] { color: #e8dcc4; border-color: #b8922c; }
.info-pop { margin-top: 6px; padding: 8px 10px; border: 1px solid rgba(184,146,44,0.3);
  border-radius: 3px; background: #1a1410; color: var(--ink-2); font-size: var(--fs-2); line-height: 1.5; }
#app.sb-hidden #sidebar, #app.sb-hidden #sb-resizer { display: none; }
#app.sb-hidden #sb-float { display: flex; }
[data-collapsible] { cursor: pointer; user-select: none; }
[data-collapsible]::before { content: "\\25BE\\00a0"; }
[data-collapsible].sec-collapsed::before { content: "\\25B8\\00a0"; }
.sec-hide { display: none !important; }
/* Search row */
#ws-search-row { position: relative; padding: 10px 0 12px; flex-shrink: 0; }
#ws-search-wrap { position: relative; }
#ws-search-icon { position: absolute; left: 8px; top: 50%; transform: translateY(-50%);
  color: var(--muted); font-size: var(--fs-2); pointer-events: none; line-height: 1; }
#ws-search { width: 100%; background: #1a1410; border: 1px solid rgba(184,146,44,0.25);
  color: #e8dcc4; padding: 5px 8px 5px 24px; font-size: var(--fs-2); border-radius: 2px;
  font-family: inherit; outline: none; }
#ws-search:focus { border-color: rgba(184,146,44,0.7); }
#ws-search-drop { position: absolute; top: 100%; left: 0; right: 0;
  background: rgba(18,12,5,0.97); border: 1px solid rgba(184,146,44,0.4);
  border-top: none; border-radius: 0 0 4px 4px; max-height: 240px; overflow-y: auto; z-index: 30;
  box-shadow: 2px 6px 18px rgba(0,0,0,0.7); }
.wsd-group { font-size: var(--fs-1); text-transform: uppercase; letter-spacing: 0.1em;
  color: var(--muted); padding: 5px 10px 2px; border-top: 1px solid rgba(184,146,44,0.1); }
.wsd-group:first-child { border-top: none; }
.wsd-item { padding: 5px 12px; font-size: var(--fs-2); cursor: pointer; color: #c8b890;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.wsd-item:hover { background: rgba(184,146,44,0.12); color: #e8dcc4; }
.wsd-empty { padding: 8px 12px; font-size: var(--fs-2); color: var(--muted); font-style: italic; }
/* Travel time tab */
.tt-presets { display:flex; gap:3px; flex-wrap:wrap; }
.tt-preset { flex:1 1 auto; white-space:nowrap; padding:6px 6px; font-size: var(--fs-1); letter-spacing:0.02em;
  text-transform:uppercase; background:#1a1408; border:1px solid rgba(184,146,44,0.2);
  color:var(--muted); border-radius:2px; cursor:pointer; }
.tt-preset:hover { color:#c8a84a; border-color:rgba(184,146,44,0.45); }
.tt-preset.active { background:#0a0805; color:#e8dcc4; border-color:rgba(184,146,44,0.45);
  font-weight:bold; }
.tt-state { font-size: var(--fs-2); color:var(--muted); margin-bottom:6px; min-height:14px; }
.tt-state b { color:var(--warn); font-weight:normal; }
#tt-actions { flex-wrap:nowrap; gap:6px; align-items:center; }
#tt-actions .btn { padding:8px 10px; white-space:nowrap; }
#tt-actions #tt-lock-btn { color:#8fd18f; background:transparent; border:none; padding:6px 4px; min-width:0; }
#tt-actions #tt-lock-btn.armed { color:#f0877a; background:transparent; }
.tt-lockword { color:#f0877a; text-decoration:line-through; }
.tt-lockword.open { color:#8fd18f; text-decoration:none; }
#tt-lock-btn svg { width:18px; height:18px; display:block; margin:0 auto; }
.tt-stops-list { display:flex; flex-direction:column; gap:0; }
.tt-stop-row { display:flex; align-items:center; gap:6px; padding:4px 6px;
  background:#1a1408; border-radius:3px; border:1px solid rgba(184,146,44,0.12);
  margin-bottom:1px; }
.tt-stop-num { width:18px; height:18px; border-radius:50%; background:#3a5a3a;
  display:flex; align-items:center; justify-content:center;
  font-size: var(--fs-1); font-weight:bold; color:#fff; flex-shrink:0; }
.tt-stop-name { flex:1; font-size: var(--fs-2); color:#c8b87a; font-style:italic;
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.tt-stop-rm { background:none; border:none; color:var(--muted); cursor:pointer;
  font-size: var(--fs-2); padding:0 2px; line-height:1; flex-shrink:0; }
.tt-stop-rm:hover { color:var(--warn); }
.tt-leg-row { padding:3px 6px 3px 30px; font-size: var(--fs-2); display:grid;
  grid-template-columns:auto auto 1fr; gap:4px; align-items:center; color:var(--muted); }
.tt-leg-row select { background-color:#1a1408; border:1px solid rgba(184,146,44,0.25);
  color:#c8b87a; padding:2px 3px; border-radius:2px; font-size: var(--fs-2); min-width:0; }
.tt-leg-row select option { background:#1a1410; }
.tt-leg-row select option:disabled { color:var(--muted); }
.tt-leg-res { color:#c8a84a; text-align:right; white-space:nowrap; overflow:hidden;
  text-overflow:ellipsis; }
.tt-leg-row.fetching .tt-leg-txt { opacity:0.55; font-style:italic; }
.tt-leg-row.fallback .tt-leg-res { color:var(--warn); }
.tt-leg-cancel { background:none; border:1px solid rgba(184,146,44,0.3); color:#c8b87a;
  cursor:pointer; font-size: var(--fs-2); padding:0 4px; margin-left:5px; border-radius:2px; }
.tt-leg-cancel:hover { color:var(--warn); border-color:var(--warn); }
.tt-totals { border-top:1px solid rgba(184,146,44,0.18); padding:6px 0 0;
  display:grid; grid-template-columns:60px 1fr 1fr; gap:3px; font-size: var(--fs-2); }
.tt-saved { display:flex; flex-direction:column; gap:2px; }
.tt-saved-row { display:flex; align-items:center; gap:6px; padding:3px 6px;
  background:#1a1408; border:1px solid rgba(184,146,44,0.12); border-radius:3px;
  font-size: var(--fs-2); color:#c8b87a; }
.tt-saved-row.current { border-color:rgba(232,160,96,0.55); }
.tt-saved-name { cursor:pointer; flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.tt-saved-meta { color:var(--muted); font-size: var(--fs-2); white-space:nowrap; }
.tt-saved-meta.gm { color:#b08a58; }
.tt-saved-row button { background:none; border:1px solid rgba(184,146,44,0.25); color:var(--muted);
  border-radius:2px; cursor:pointer; font-size: var(--fs-2); padding:1px 5px; }
.tt-saved-row button:hover { color:#e8dcc4; border-color:rgba(184,146,44,0.55); }
.tt-saved-row button.armed { color:var(--warn); border-color:var(--danger); }
.tt-tot-lbl { color:var(--muted); padding-top:2px; }
.tt-tot-v { color:#c8b87a; font-family:monospace; }
.tt-tot-t { color:#e8dcc4; font-weight:bold; }
.tt-map-pin { width:22px; height:22px; border-radius:50%; display:flex; align-items:center;
  justify-content:center; font-size: var(--fs-1); font-weight:bold; color:#fff; cursor:grab;
  border:2px solid rgba(255,255,255,0.7); box-shadow:0 2px 6px rgba(0,0,0,0.5); }
/* Player share bar */
#player-share { display:none; align-items:center; gap:6px; padding:4px 10px;
  background:rgba(90,160,90,0.12); border-bottom:1px solid rgba(90,160,90,0.2);
  font-size: var(--fs-2); color:#7ab07a; }
#player-share a { color:#8ad08a; font-family:monospace; font-size: var(--fs-2);
  overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
#player-share-copy { background:none; border:1px solid rgba(90,160,90,0.3);
  color:#7ab07a; padding:2px 6px; border-radius:2px; cursor:pointer; font-size: var(--fs-2); }
#player-share-copy:hover { background:rgba(90,160,90,0.15); }
"""


def _build_panel_plan_route() -> str:
    return """
<button type="button" class="btn btn-sm arm-btn" data-arm="route" aria-pressed="false">＋ Add stops from map</button>
<p class="hint" style="color:#9a8a6a;">Arm it, then click location markers to add waypoints. Esc stops.</p>
<ul id="route-queue-list"><li class="queue-empty">No waypoints yet.</li></ul>
<div class="btn-row">
  <button id="route-remove-btn" class="btn btn-sm btn-danger" disabled>Remove Last</button>
  <button id="route-clear-btn" class="btn btn-sm btn-danger" disabled>Clear All</button>
</div>
<div class="field-group" style="margin-top:4px;">
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
<p id="route-status" class="hint" style="margin-top:2px;"></p>
<p class="hint" style="color:#9a8a6a;">Requires devserver: <code>venv/bin/python utilities/devserver.py</code><br>
Adds segments, snaps to roads, rebuilds workshop automatically.</p>
"""


def _build_panel_inspector(region_options: str) -> str:
    # One docked form for both jobs: a selected pin is "Editing X", nothing selected is
    # "New location". Every canonical Type is selectable; a page whose Type is off the
    # list shows the disabled placeholder, which Save never sends (see _EF_DIFF_JS).
    type_opts = '      <option value="" disabled>(not on the list)</option>\n' + "\n".join(
        f'      <option value="{c}">{"POI" if c == "poi" else c.replace("-", " ").title()}</option>'
        for c in CATEGORIES
    )
    icon_opts = "\n".join(
        f'      <option value="{v}">{label}</option>'
        for v, label in [("", "From Type"), *((n, n) for n in ICON_NAMES), ("none", "none (hidden)")]
    )
    return f"""
<div class="insp-head">
  <div class="list-heading"><span id="ef-mode">New location</span> <span id="ef-slug" class="insp-slug"></span></div>
  <button id="ef-close-btn" type="button" class="close-x hidden" title="Close (Esc)" aria-label="Close">✕</button>
</div>
<div class="field-group">
  <label>Coordinates</label>
  <div class="coord-row">
    <span>lat</span><input id="ef-lat" type="text" readonly placeholder="—">
    <span>lon</span><input id="ef-lon" type="text" readonly placeholder="—">
    <button id="ef-place-btn" type="button" class="btn btn-sm arm-btn ef-create-only" data-arm="place" aria-pressed="false" title="Pick on map">◎ Pick</button>
    <button id="ef-move-btn" type="button" class="btn btn-sm ef-edit-only hidden">Move</button>
  </div>
</div>
<div class="field-group">
  <label>Name <span class="ef-create-only">*</span></label>
  <input id="ef-name" type="text" placeholder="Nur-Ata">
</div>
<div class="field-group">
  <label>Fantasy Name <span class="insp-note">(blank = use real name)</span></label>
  <input id="ef-fantasy" type="text" placeholder="optional">
</div>
<div class="field-group">
  <label>Type <span class="ef-create-only">*</span></label>
  <select id="ef-type">
{type_opts}
  </select>
</div>
<div class="field-group ef-edit-only hidden">
  <label>Icon override</label>
  <select id="ef-icon">
{icon_opts}
  </select>
  <p id="ef-icon-note" class="ef-icon-note"></p>
</div>
<div class="field-group">
  <label>Visibility</label>
  <div class="radio-row">
    <label><input type="radio" name="ef-vis" value="public"> public</label>
    <label><input type="radio" name="ef-vis" value="gm_secrets" checked> GM only</label>
  </div>
</div>
<div class="field-group ef-create-only">
  <label>Region</label>
  <select id="ef-region">
    <option value="">— none —</option>
    {region_options}
  </select>
</div>
<div class="field-group ef-create-only">
  <label>Description</label>
  <textarea id="ef-desc" rows="2" placeholder="optional"></textarea>
</div>
<details id="ef-adv" class="ef-adv ef-edit-only hidden">
  <summary>Advanced</summary>
  <p class="hint">Every other frontmatter key on the page. Edit scalars here; lists and nested values are shown read-only.</p>
  <p id="ef-adv-status" class="hint"></p>
  <div id="ef-adv-scalars"></div>
  <div id="ef-adv-readonly"></div>
</details>
<div class="btn-row insp-actions">
  <button id="ef-save-btn" type="button" class="btn" disabled>Create Location</button>
</div>
<p id="ef-status" class="hint insp-status"></p>
<p class="hint insp-note">Requires devserver: <code>venv/bin/python utilities/devserver.py</code></p>
<div id="unsaved-section" class="hidden" style="margin-top:2px;">
  <div class="list-heading" data-collapsible>Saved This Session</div>
  <ul id="unsaved-list"></ul>
</div>
<div class="rebuild-section">
  <div class="list-heading" data-collapsible>Rebuild</div>
  <div class="btn-row">
    <button id="rebuild-locations-btn" class="btn btn-sm">Rebuild Locations</button>
    <button id="rebuild-workshop-btn" class="btn btn-sm">Rebuild Workshop</button>
  </div>
  <p id="api-status" class="hint" style="margin-top:2px;"></p>
</div>
"""


def _build_panel_batch() -> str:
    """The batch bar: shown inside the Inspector panel while 2+ locations are selected."""
    return """
<div id="ms-bar" class="hidden">
  <div class="insp-head">
    <div class="list-heading"><span id="ms-count">0 selected</span></div>
    <button id="ms-clear-btn" type="button" class="btn btn-sm" title="Clear selection (Esc)">Clear</button>
  </div>
  <p class="hint insp-note">Shift-, Ctrl- or Cmd-click pins to add or remove them. Nothing is written until you confirm.</p>
  <ul id="ms-list"></ul>
  <div class="btn-row">
    <button id="ms-add-hidden-btn" type="button" class="btn btn-sm" title="Add every GM-only pin in the current map view">Add GM-only in view</button>
  </div>
  <div class="btn-row">
    <button id="ms-public-btn" type="button" class="btn">Set to Public</button>
    <button id="ms-gm-btn" type="button" class="btn">Set to GM-only</button>
  </div>
  <div id="ms-confirm" class="hidden">
    <div id="ms-confirm-msg"></div>
    <ul id="ms-confirm-list"></ul>
    <div class="btn-row">
      <button id="ms-confirm-yes" type="button" class="btn btn-sm">Confirm</button>
      <button id="ms-confirm-no" type="button" class="btn btn-sm">Cancel</button>
    </div>
  </div>
  <p id="ms-status" class="hint"></p>
</div>
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
<p class="hint" style="color:#9a8a6a;margin-bottom:6px;">Click map or a location to add stops. Drag markers to reposition. Every leg has its own mode and path.</p>
<div id="tt-state" class="tt-state"></div>
<div id="tt-stops-list" class="tt-stops-list"></div>
<div id="tt-totals" class="tt-totals" hidden>
  <span class="tt-tot-lbl">Total</span>
  <span class="tt-tot-v" id="tt-tot-dist">—</span>
  <span class="tt-tot-t" id="tt-tot-time">—</span>
</div>
<div class="field-group" style="margin-top:4px;">
  <label>Mode for new legs / all legs</label>
  <div class="tt-presets">
    __TT_PRESETS__
  </div>
  <select id="tt-all-path">
    <option value="">Path: keep each leg's own</option>
    __TT_PATH_OPTS__
  </select>
</div>
<div id="tt-form" hidden>
<div class="field-group" style="margin-top:4px;">
  <label for="tt-name">Journey name</label>
  <input id="tt-name" type="text" maxlength="__TT_MAX_NAME__" placeholder="e.g. Spring caravan to Merv" autocomplete="off">
</div>
<div class="field-group" style="margin-top:12px;">
  <label for="tt-vis">Visible to players</label>
  <select id="tt-vis">
    <option value="gm_secrets">GM only</option>
    <option value="public">Players (once every stop is public)</option>
  </select>
</div>
<div id="tt-actions" class="btn-row" style="margin-top:14px;">
  <button id="tt-lock-btn" class="btn btn-sm" aria-pressed="false" aria-label="Lock journey" title="Lock journey"></button>
  <button id="tt-save-btn" class="btn btn-sm" disabled>Save</button>
  <button id="tt-saveas-btn" class="btn btn-sm" hidden>Create new</button>
  <button id="tt-clear-btn" class="btn btn-sm btn-danger" hidden>Clear All</button>
</div>
</div>
<p id="tt-status" class="hint" style="margin-top:4px;min-height:14px;"></p>
<div class="field-group" style="margin-top:10px;">
  <label>Saved journeys</label>
  <div id="tt-saved" class="tt-saved"></div>
</div>
<p class="hint" style="color:#9a8a6a;margin-top:8px;">Saved to <code>world/data/tarim-shaiel-journeys.geojson</code> via the devserver. Time is computed from length, mode and path; it is never stored.</p>
<p class="hint" style="color:#9a8a6a;margin-top:6px;"><b>Terrain</b> routing <button type="button" class="info-btn" aria-controls="tt-terrain-info" aria-expanded="false" title="How Terrain routing works" aria-label="How Terrain routing works">i</button></p>
<div id="tt-terrain-info" class="info-pop" hidden><b>Terrain</b> walks the ground, not the roads: a least-cost path over elevation tiles, slower on slopes, with a per-mode slope limit (a cart refuses what a walker climbs). Rivers and lakes are not obstacles and existing roads are ignored. Limits and speeds are assumptions. Elevation: U.S. Geological Survey (SRTM, GMTED2010) via AWS Terrain Tiles; tiles are cached in this browser.</div>
"""
    path_opts = "\n    ".join(
        f'<option value="{p}">{p.capitalize()}</option>'
        for p in journeys.LEG_PATHS
    )
    return (html.replace("__TT_PRESETS__", _tt_presets_html())
                .replace("__TT_PATH_OPTS__", path_opts)
                .replace("__TT_MAX_NAME__", str(journeys.MAX_NAME)))


# Field editor Save: the form sends only the fields the GM changed. The server removes a
# key whose value is null, so sending every field wrote null for anything the form could
# not show (a Fantasy name equal to the title, an Icon override value off the list) and
# deleted the line from the file. base is what the controls showed when the page opened;
# cur is what they show now. Pure, so tests run it under node.
_WS_LATLON_JS = r"""
function _wsParseLatLon(q){
  var m=/^\s*(-?\d+(?:\.\d+)?)\s*[,;\s]\s*(-?\d+(?:\.\d+)?)\s*$/.exec(q||"");
  if(!m)return null;
  var a=parseFloat(m[1]),b=parseFloat(m[2]);
  if(Math.abs(a)<=90&&Math.abs(b)<=180)return {lat:a,lon:b};
  if(Math.abs(b)<=90&&Math.abs(a)<=180)return {lat:b,lon:a};
  return null;
}
"""

_WS_MODE_JS = r"""
function _wsModeNext(cur,ev,tab){
  if(ev==="esc"||ev==="placed")return "select";
  if(ev==="arm-place")return cur==="place"?"select":"place";
  if(ev==="arm-route")return cur==="route"?"select":"route";
  if(ev==="tab"){
    if(cur==="place"&&tab!=="inspector")return "select";
    if(cur==="route"&&tab!=="route-index")return "select";
  }
  return cur;
}
var _wsMode="select";
var _WS_MODE_LABEL={place:"Place: click the map to set the point",route:"Route: click locations to add stops"};
window._wsSetMode=function(ev,tab){
  var nxt=_wsModeNext(_wsMode,ev,tab||_activeTab);
  if(nxt==="place"&&typeof _ttStepAside==="function"&&!_ttStepAside())return;
  _wsMode=nxt;
  var chip=document.getElementById("ws-mode-chip");
  if(chip){
    chip.hidden=_wsMode==="select";
    document.getElementById("ws-mode-label").textContent=_WS_MODE_LABEL[_wsMode]||"";
  }
  document.body.classList.toggle("mode-place",_wsMode==="place");
  document.body.classList.toggle("mode-route",_wsMode==="route");
  document.querySelectorAll("[data-arm]").forEach(function(b){
    b.setAttribute("aria-pressed",b.dataset.arm===_wsMode?"true":"false");});
};
document.querySelectorAll("[data-arm]").forEach(function(b){
  b.addEventListener("click",function(){_wsSetMode("arm-"+b.dataset.arm);});});
document.getElementById("ws-mode-cancel").addEventListener("click",function(){_wsSetMode("esc");});
document.addEventListener("keydown",function(e){
  if(e.key==="Escape"&&_wsMode!=="select"){e.preventDefault();_wsSetMode("esc");}});
"""

# The inspector's form logic: one set of fields for New location and Editing X. A pin
# selects it; Close or Esc deselects. Save sends only what the GM changed (_efDiff, the
# #336 guard) from the core fields and from Advanced, in one PATCH.
_INSPECTOR_JS = r"""
function _efRead(){
  return {name:_efName.value.trim(),
  fantasy_name:_efFantasy.value.trim(),
  type:_efType.value,
  map_icon:_efIcon.value,
  visibility:document.querySelector('input[name="ef-vis"]:checked').value};
}
function _efSetVis(v){
  document.querySelectorAll('input[name="ef-vis"]').forEach(function(r){r.checked=r.value===v;});
}
function _efSync(){
  if(_efSlug){_efSaveBtn.disabled=false;return;}
  _efSaveBtn.disabled=!(_efLat.value&&_efLon.value&&_efName.value.trim()&&_efType.value);
}
function _efSetMode(slug){
  var edit=!!slug;
  _efModeEl.textContent=edit?"Editing":"New location";
  _efSlugEl.textContent=slug||"";
  _efCloseBtn.classList.toggle("hidden",!edit);
  _efCreateOnly.forEach(function(n){n.classList.toggle("hidden",edit);});
  _efEditOnly.forEach(function(n){n.classList.toggle("hidden",!edit);});
  _efSaveBtn.textContent=edit?"Save Fields":"Create Location";
  _efTypePlaceholder.textContent=edit?"(not on the list)":"— select —";
  _efSync();
}
function _efSetStatus(msg,cls){_efStatus.textContent=msg;_efStatus.className="hint"+(cls?" "+cls:"");}
function _efReset(){
  _efSlug=null;_efBase=null;_efCurrentCoords=null;_efOpenCat="";
  _efName.value="";_efFantasy.value="";_efType.value="";_efIcon.value="";
  _efRegion.value="";_efDesc.value="";_efLat.value="";_efLon.value="";
  _efSetVis("gm_secrets");
  _efAdvClear();
  if(_dragMarker){_dragMarker.remove();_dragMarker=null;}
  _efSetStatus("");
  _efSetMode(null);_efShowIcon();
}

// -- Advanced: the page's other frontmatter. Scalars edit; lists and nested values show.
function _efAdvClear(){
  _efAdvBase=null;_efAdvBad=null;
  _efAdvScalars.textContent="";_efAdvReadonly.textContent="";_efAdvStatus.textContent="";
}
function _efAdvRow(key,val){
  var row=document.createElement("div");row.className="field-group adv-row";
  var lab=document.createElement("label");lab.textContent=key;row.appendChild(lab);
  var inp;
  if(typeof val==="boolean"){
    inp=document.createElement("input");inp.type="checkbox";inp.checked=val;inp.dataset.t="bool";
    lab.className="adv-check";lab.insertBefore(inp,lab.firstChild);
  }else{
    var multi=typeof val==="string"&&(val.indexOf("\n")!==-1||val.length>70);
    inp=document.createElement(multi?"textarea":"input");
    if(multi)inp.rows=3;else inp.type="text";
    inp.value=val==null?"":String(val);
    inp.dataset.t=typeof val==="number"?"num":"str";
    row.appendChild(inp);
  }
  inp.dataset.key=key;
  inp.addEventListener("input",_efSync);
  return row;
}
function _efAdvValues(){
  var out={};_efAdvBad=null;
  _efAdvScalars.querySelectorAll("[data-key]").forEach(function(el){
    var k=el.dataset.key,t=el.dataset.t,v;
    if(t==="bool")v=el.checked;
    else if(t==="num"){
      if(el.value.trim()==="")v="";
      else{v=Number(el.value);if(isNaN(v)){_efAdvBad=k;v=el.value;}}
    }else v=el.value;
    out[k]=v;});
  return out;
}
function _efAdvDiff(){
  if(!_efAdvBase)return {};
  var d=_efDiff(_efAdvBase,_efAdvValues());
  Object.keys(d).forEach(function(k){if(d[k]==="")d[k]=null;});
  return d;
}
function _efAdvLoad(){
  _efAdvClear();
  if(!_efSlug||!_efAdv.open)return;
  var slug=_efSlug;
  _efAdvStatus.textContent="Loading…";
  fetch("/api/locations/"+encodeURIComponent(slug)+"/frontmatter")
  .then(function(r){return r.json();})
  .then(function(d){
    if(_efSlug!==slug)return;
    if(!d.ok){_efAdvStatus.textContent="✗ "+(d.error||"error");return;}
    _efAdvStatus.textContent="";
    Object.keys(d.scalars).forEach(function(k){_efAdvScalars.appendChild(_efAdvRow(k,d.scalars[k]));});
    Object.keys(d.readonly).forEach(function(k){
      var row=document.createElement("div");row.className="adv-ro";
      var lab=document.createElement("div");lab.className="adv-ro-key";lab.textContent=k+" (read-only)";
      var pre=document.createElement("pre");pre.textContent=JSON.stringify(d.readonly[k],null,1);
      row.appendChild(lab);row.appendChild(pre);_efAdvReadonly.appendChild(row);});
    _efAdvBase=_efAdvValues();
  })
  .catch(function(){if(_efSlug===slug)_efAdvStatus.textContent="✗ Network error — devserver running?";});
}
_efAdv.addEventListener("toggle",_efAdvLoad);

// -- Selecting and deselecting
function _efDirty(){
  if(_efSlug)return !!(_efBase&&Object.keys(_efDiff(_efBase,_efRead())).length)||Object.keys(_efAdvDiff()).length>0;
  return !!(_efName.value.trim()||_efFantasy.value.trim()||_efType.value||_efLat.value||_efDesc.value.trim());
}
function _efConfirmDiscard(){return !_efDirty()||confirm("Discard unsaved changes?");}
function _efClose(){if(!_efConfirmDiscard())return;_efReset();}

function _openFieldEditor(feature){
  if(_activeTab!=="inspector")_setTab("inspector");
  if(typeof _selectedRouteId!=="undefined"&&_selectedRouteId)_hideRoutePanel();
  var p=feature.properties;
  var slug=p.slug||p._slug||"";
  if(slug===_efSlug)return;
  if(!_efConfirmDiscard())return;
  _efSlug=slug;
  _efCurrentCoords={lng:feature.geometry.coordinates[0],lat:feature.geometry.coordinates[1]};
  _efLat.value=_efCurrentCoords.lat.toFixed(6);
  _efLon.value=_efCurrentCoords.lng.toFixed(6);
  _efName.value=p.title||"";
  var fn=p.fantasyName||(p.label!==p.title?p.label:"");
  _efFantasy.value=(fn&&fn!==p.title)?fn:"";
  if(_efType.querySelector('option[value="'+p.category+'"]'))_efType.value=p.category;
  else _efType.value="";
  _efOpenCat=p.category||"";
  var mm=p.mapMarker;
  var mmVal=mm===false?"none":(mm||"");
  if(_efIcon.querySelector('option[value="'+mmVal+'"]'))_efIcon.value=mmVal;
  else _efIcon.value="";
  _efSetVis(p.visibility==="gm_secrets"?"gm_secrets":"public");
  _efSetStatus("");
  _efSetMode(slug);
  _efShowIcon();_efBase=_efRead();
  _efAdvLoad();
}
"""

_INSPECTOR_WIRE_JS = r"""
// Place mode: one click sets the coordinates, then back to Select
map.on("click",function(e){
  if(_wsMode!=="place")return;
  window._wsJustPlaced=true;setTimeout(function(){window._wsJustPlaced=false;},0);
  _efLat.value=e.lngLat.lat.toFixed(6);
  _efLon.value=e.lngLat.lng.toFixed(6);
  _wsSetMode("placed");
  _efSync();
});
[_efName,_efType,_efFantasy].forEach(function(el){
  el.addEventListener("input",_efSync);el.addEventListener("change",_efSync);});

function _efCreate(){
  var lat=_efLat.value,lon=_efLon.value,name=_efName.value.trim(),typ=_efType.value;
  if(!lat||!lon||!name||!typ)return;
  var body={name:name,lat:parseFloat(lat),lon:parseFloat(lon),category:typ,
    fantasy_name:_efFantasy.value.trim(),region:_efRegion.value,
    visibility:document.querySelector('input[name="ef-vis"]:checked').value,
    description:_efDesc.value.trim()};
  _efSetStatus("Creating…");_efSaveBtn.disabled=true;
  fetch("/api/locations/create",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})
  .then(function(r){return r.json();})
  .then(function(d){
    if(!d.ok){_efSync();_efSetStatus("✗ "+(d.error||d.output||"unknown"),"err");return;}
    _efReset();
    _efSetStatus("✓ Created. Rebuilding workshop…","ok");
    fetch("/api/rebuild/workshop",{method:"POST"}).then(function(){
      _efSetStatus("✓ Created — reload to see the new pin.","ok");});
  })
  .catch(function(){_efSync();_efSetStatus("✗ Devserver not running.","err");});
}

_efSaveBtn.addEventListener("click",function(){
  if(!_efSlug){_efCreate();return;}
  if(!_efBase)return;
  var slug=_efSlug,cur=_efRead(),fields=_efDiff(_efBase,cur);
  var advCur=_efAdvValues(),adv=_efAdvDiff();
  if(_efAdvBad){_efSetStatus("✗ "+_efAdvBad+" must be a number","err");return;}
  Object.keys(adv).forEach(function(k){fields[k]=adv[k];});
  if(!Object.keys(fields).length){
    _efStatus.textContent="No changes";_efStatus.className="hint";return;}
  _patchFrontmatter(slug,fields,function(){if(_efSlug===slug){_efBase=cur;_efAdvBase=advCur;}});
});

_efMoveBtn.addEventListener("click",function(){
  if(!_efSlug||!_efCurrentCoords)return;
  _startDragEdit(_efSlug,_efCurrentCoords);
});
_efCloseBtn.addEventListener("click",_efClose);
document.addEventListener("keydown",function(e){
  if(e.key==="Escape"&&!e.defaultPrevented&&_wsMode==="select"&&_selectedRouteId&&!_msSel.length){_hideRoutePanel();return;}
  if(e.key!=="Escape"||e.defaultPrevented||_wsMode!=="select"||!_efSlug||_msSel.length)return;
  if(document.querySelector(".info-btn[aria-expanded=true]"))return;
  _efClose();
});
_efReset();
"""


_EF_DIFF_JS = r"""
function _efDiff(base,cur){
  var out={};
  Object.keys(cur).forEach(function(k){
    if(base[k]===cur[k])return;
    if(k==="type"&&!cur[k])return;
    var v=cur[k];
    if(k==="fantasy_name"&&v==="")v=null;
    if(k==="map_icon"&&v==="")v=null;
    out[k]=v;
  });
  return out;
}
"""


# The Icon override's readout: the icon the pin will draw with, and where it comes from.
# The Type select is blank for a page whose Type is off the list, so the readout falls
# back to the page's own category. A Type no tier draws has no pin whatever the override.
_EF_ICON_NOTE_JS = r"""
function _efShowIcon(){
  var ov=_efIcon.value,from=_efTypeIcons[_efType.value||_efOpenCat],txt;
  if(!_efType.value&&!_efOpenCat)txt="Icon: pick a Type first";
  else if(!from)txt="No pin: this Type is not drawn";
  else if(ov==="none")txt="Icon: hidden (override)";
  else if(ov)txt="Icon: "+ov+" (override)";
  else txt="Icon: "+from+" (from Type)";
  _efIconNote.textContent=txt;
}
_efType.addEventListener("change",_efShowIcon);
_efIcon.addEventListener("change",_efShowIcon);
"""


# Multi-select and the batch bar (#353): Shift/Ctrl/Cmd-click pins to select several, then
# set their visibility together. Nothing touches a file until the GM confirms, and the
# rebuild runs once for the whole batch. Raw string; spliced into _build_app_js.
_MULTISELECT_JS = r"""
var _msSel=[];
var _msErr={};
var _msBusy=false;
var _msBar=document.getElementById("ms-bar");
var _msListEl=document.getElementById("ms-list");
var _msCountEl=document.getElementById("ms-count");
var _msStatusEl=document.getElementById("ms-status");
var _msConfirmEl=document.getElementById("ms-confirm");
var _msConfirmMsg=document.getElementById("ms-confirm-msg");
var _msConfirmList=document.getElementById("ms-confirm-list");
var _msPubBtn=document.getElementById("ms-public-btn");
var _msGmBtn=document.getElementById("ms-gm-btn");
var _msPending=null;

function _msEsc(s){
  return String(s==null?"":s).replace(/[&<>"']/g,function(c){
    return{"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c];});
}
function _msIsPublic(l){return !!l&&l.visibility==="public";}
function _msName(l){return l.label||l.title||l.slug;}
function _msSetStatus(msg,cls){_msStatusEl.textContent=msg;_msStatusEl.className="hint"+(cls?" "+cls:"");}

function _msUpdateRings(){
  var src;
  try{src=map.getSource("reveal-source");}catch(e){return;}
  if(!src)return;
  var feats=[];
  _msSel.forEach(function(s){
    var l=_locBySlug[s];
    if(l)feats.push({type:"Feature",properties:{state:"staged"},
      geometry:{type:"Point",coordinates:[l.lon,l.lat]}});
  });
  src.setData({type:"FeatureCollection",features:feats});
}

function _msRefresh(){
  var n=_msSel.length;
  var multi=n>=2;
  document.body.classList.toggle("ms-multi",multi);
  _msBar.classList.toggle("hidden",!multi);
  _msCountEl.textContent=n+" selected";
  _msPubBtn.disabled=_msBusy;_msGmBtn.disabled=_msBusy;
  if(!multi)_msConfirmEl.classList.add("hidden");
  _msListEl.innerHTML=_msSel.map(function(s){
    var l=_locBySlug[s];
    var err=_msErr[s]?'<div class="ms-err">✗ '+_msEsc(_msErr[s])+'</div>':"";
    return '<li class="queue-item ms-item"><div class="ms-main">'+
      '<button class="ms-name" data-fly="'+_msEsc(s)+'">'+_msEsc(_msName(l))+'</button> '+
      '<span class="ms-vis">'+(_msIsPublic(l)?"public":"GM-only")+'</span>'+err+'</div>'+
      '<button class="ms-x" data-slug="'+_msEsc(s)+'" title="Remove from selection">✕</button></li>';}).join("");
  _msUpdateRings();
}

function _msToggle(slug){
  if(_msBusy||!_locBySlug[slug])return;
  if(!_msSel.length&&_efSlug&&_efSlug!==slug&&_locBySlug[_efSlug])_msSel.push(_efSlug);
  var i=_msSel.indexOf(slug);
  if(i===-1)_msSel.push(slug);else _msSel.splice(i,1);
  delete _msErr[slug];
  _msConfirmEl.classList.add("hidden");
  _msSetStatus("","");
  _msRefresh();
}
window._msClear=function(){
  if(_msBusy)return;
  _msSel=[];_msErr={};_msSetStatus("","");_msRefresh();
};

function _msInView(){
  var b=map.getBounds();
  return _locList.filter(function(l){
    return !_msIsPublic(l)&&_msSel.indexOf(l.slug)===-1&&b.contains([l.lon,l.lat]);});
}

function _msRebuild(target){
  return fetch("/api/rebuild/"+target,{method:"POST"})
    .then(function(r){return r.json();})
    .then(function(d){return !!d.ok;},function(){return false;});
}

function _msAsk(vis){
  var todo=_msSel.filter(function(s){return (_msIsPublic(_locBySlug[s])?"public":"gm_secrets")!==vis;});
  if(!todo.length){_msSetStatus("Every selected location is already "+(vis==="public"?"public":"GM-only")+".","");return;}
  _msPending={vis:vis,slugs:todo};
  _msConfirmMsg.textContent=vis==="public"?
    "Set these to public? Players will see them after the rebuild.":
    "Set these to GM-only? Players will lose them after the rebuild.";
  _msConfirmList.innerHTML=todo.map(function(s){return "<li>"+_msEsc(_msName(_locBySlug[s]))+"</li>";}).join("");
  _msConfirmEl.classList.remove("hidden");
}

function _msApply(){
  if(_msBusy||!_msPending)return;
  var vis=_msPending.vis,queue=_msPending.slugs.slice(),done=0,aborted=false;
  var verb=vis==="public"?"Revealed ":"Hid ";
  _msPending=null;
  _msBusy=true;_msErr={};
  _msConfirmEl.classList.add("hidden");
  _msSetStatus("Writing 0 of "+queue.length+"…","");
  _msRefresh();
  function step(i){
    if(i>=queue.length||aborted)return Promise.resolve();
    var slug=queue[i];
    return _patchFrontmatterRaw(slug,{visibility:vis}).then(function(d){
      if(d&&d.ok){done++;}
      else{_msErr[slug]=(d&&d.error)||"error";}
      _msSetStatus("Writing "+(i+1)+" of "+queue.length+"…","");
    },function(){
      aborted=true;
      _msErr[slug]="Network error — is the devserver running?";
    }).then(function(){return step(i+1);});
  }
  step(0).then(function(){
    _refreshLocSource();
    _msBusy=false;
    var failed=queue.length-done;
    _msSel=_msSel.filter(function(s){return !!_msErr[s];});
    if(!done){
      _msSetStatus("✗ Nothing written — "+failed+" failed.","err");
      _msRefresh();
      return;
    }
    _msSetStatus(verb+done+(failed?" · "+failed+" failed":"")+". Rebuilding…","");
    _msRefresh();
    _msRebuild("workshop").then(function(okW){
      return _msRebuild("locations").then(function(okL){return okW&&okL;});
    }).then(function(okAll){
      _msSetStatus((okAll?"✓ ":"✗ ")+verb+done+(failed?" · "+failed+" failed":"")+
        (okAll?". Player map and location pages rebuilt.":". Rebuild failed — see the devserver log."),
        (okAll&&!failed)?"ok":"err");
    });
  });
}

_msListEl.addEventListener("click",function(e){
  var x=e.target.closest(".ms-x");
  if(x){_msToggle(x.dataset.slug);return;}
  var n=e.target.closest(".ms-name");
  if(n)_wsFlyTo(_locBySlug[n.dataset.fly]);
});
document.getElementById("ms-clear-btn").addEventListener("click",window._msClear);
document.getElementById("ms-add-hidden-btn").addEventListener("click",function(){
  if(_msBusy)return;
  var add=_msInView();
  add.forEach(function(l){_msSel.push(l.slug);});
  _msConfirmEl.classList.add("hidden");
  _msSetStatus(add.length?"Added "+add.length+" GM-only in view.":"No more GM-only locations in view.","");
  _msRefresh();
});
_msPubBtn.addEventListener("click",function(){if(!_msBusy)_msAsk("public");});
_msGmBtn.addEventListener("click",function(){if(!_msBusy)_msAsk("gm_secrets");});
document.getElementById("ms-confirm-yes").addEventListener("click",_msApply);
document.getElementById("ms-confirm-no").addEventListener("click",function(){
  _msPending=null;_msConfirmEl.classList.add("hidden");});
document.addEventListener("keydown",function(e){
  if(e.key!=="Escape"||e.defaultPrevented||!_msSel.length||_msBusy)return;
  e.preventDefault();window._msClear();
});
_msRefresh();
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
// Locked journeys refuse every edit that changes stops, legs or name. Saved
// journeys load locked; a new, unsaved one starts editable.
var _ttLocked=false;
var _TT_ICON_LOCKED='<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="10" height="7" rx="1.2"/><path d="M5 7V5a3 3 0 0 1 6 0v2"/></svg>';
var _TT_ICON_OPEN='<svg viewBox="0 0 16 16" width="16" height="16" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="7" width="10" height="7" rx="1.2"/><path d="M5.2 7V3.6a3 3 0 0 1 5.6-1.5"/></svg>';
var _ttColors=["#3a6a3a","#3a4a8a","#7a3a3a","#6a5a20","#4a2a7a","#206a60","#7a4a20"];

function _ttEl(id){return document.getElementById(id);}
function _ttEsc(s){
  return String(s==null?"":s).replace(/[&<>"]/g,function(c){
    return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c];});}
function _ttSay(msg){var e=_ttEl("tt-status");if(e)e.textContent=msg||"";}
function _ttIsFly(m){var s=_TT.speeds[m];return !!(s&&s.fly);}
function _ttMarkDirty(){_ttDirty=true;}
function _ttGuard(){
  if(!_ttLocked)return false;
  _ttSay("This journey is locked. Click Unlock to edit it.");
  return true;}

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
  if(_ttGuard())return;
  var leg=_ttLegs[i];
  if(!leg||!_TT.speeds[mode])return;
  var rebuild=_ttApplyMode(leg,mode);
  _ttMarkDirty();
  if(rebuild)_ttSetLegGeom(i);else _ttRender();}

function _ttSetPath(i,path){
  if(_ttGuard())return;
  var leg=_ttLegs[i];
  if(!leg||_ttIsFly(leg.mode)||leg.path===path)return;
  leg.path=path;
  _ttMarkDirty();
  _ttSetLegGeom(i);}

// -- Stops --------------------------------------------------------------
function _ttAddMarker(i){
  var s=_ttStops[i];
  var el=_ttPinEl(i+1,_ttColors[i%_ttColors.length]);
  var mk=new maplibregl.Marker({element:el,draggable:!_ttLocked}).setLngLat([s.lng,s.lat]).addTo(map);
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
  if(_ttGuard())return;
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
  if(_ttGuard())return;
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
  _ttJid=null;_ttDirty=false;_ttLocked=false;_ttDisarm();
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
  if(_ttJid)st.innerHTML='<span class="tt-lockword'+(_ttLocked?'':' open')+'">Editing</span>'+" <b>"+_ttEsc(f?f.properties.name:_ttJid)+"</b>"+(_ttDirty?" — unsaved changes":"");
  else if(_ttStops.length)st.textContent="New journey — not saved yet";
  else st.textContent="New journey — add two or more stops";
  var busy=_ttLegs.some(function(l){return l.state==="fetching";});
  var save=_ttEl("tt-save-btn"),as=_ttEl("tt-saveas-btn");
  save.disabled=_ttStops.length<2||busy;
  save.textContent=_ttJid?"Save changes":"Save";
  as.hidden=!_ttJid;as.disabled=save.disabled;
  _ttApplyLock();}

function _ttApplyLock(){
  var lk=_ttEl("tt-lock-btn");
  if(lk){
    var lbl=_ttLocked?"Unlock journey":"Lock journey";
    lk.innerHTML=_ttLocked?_TT_ICON_LOCKED:_TT_ICON_OPEN;
    lk.title=lbl;lk.setAttribute("aria-label",lbl);
    lk.classList.toggle("armed",_ttLocked);
    lk.setAttribute("aria-pressed",_ttLocked?"true":"false");}
  _ttMarkers.forEach(function(mk){mk.setDraggable(!_ttLocked);});
  var f=_ttEl("tt-form");
  if(f)f.classList.toggle("tt-locked",_ttLocked);
  ["tt-name","tt-all-path"].forEach(function(id){var e=_ttEl(id);if(e)e.disabled=_ttLocked;});
  document.querySelectorAll(".tt-preset,.tt-stop-rm,.tt-leg-mode,.tt-leg-path").forEach(function(e){
    e.disabled=_ttLocked;});}

function _ttToggleLock(){
  _ttLocked=!_ttLocked;
  _ttApplyLock();_ttRenderState();
  if(!_ttJid){_ttSay(_ttLocked?"Locked.":"Unlocked.");return;}
  var want=_ttLocked,id=_ttJid;
  fetch("/api/journeys/"+encodeURIComponent(id),{method:"PATCH",
    headers:{"Content-Type":"application/json"},body:JSON.stringify({locked:want})})
  .then(function(r){return r.json().then(function(d){return {ok:r.ok,d:d};});})
  .then(function(x){
    if(!x.ok||!x.d.ok){_ttSay((x.d&&x.d.error)||"Could not save the lock.");return;}
    _ttStore(x.d.journey,x.d.popup);_ttRenderSaved();
    _ttSay(want?"Locked.":"Unlocked. Save re-locks it.");})
  .catch(function(){_ttSay("Devserver not reachable. Run venv/bin/python utilities/devserver.py");});}

// Leaving the Journeys tab only locks the loaded journey. Local only, the saved
// lock flag is the user's to change.
function _ttRelock(){
  if(!_ttJid||_ttLocked)return;
  _ttLocked=true;_ttApplyLock();_ttRenderState();}
// An edit or create action (a route, a pin, place mode) takes over from the
// loaded journey. A clean one unloads; one with unsaved changes asks first.
// Returns false when the user cancels, so the caller drops the new action.
function _ttStepAside(){
  if(!_ttJid)return true;
  if(_ttDirty&&!confirm("Discard unsaved journey changes?"))return false;
  _ttClear();return true;}

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
  _ttEl("tt-form").hidden=_ttStops.length===0;
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

function _ttFilterSaved(){_dispApply();}

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
    row.querySelector(".tt-saved-name").addEventListener("click",function(){_ttLoad(id);});
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
  _ttJid=id;_ttDirty=moved.length>0;_ttLocked=p.locked!==false;
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
  var body={name:name,visibility:_ttEl("tt-vis").value,locked:true,
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
    _ttJid=x.d.journey.id;_ttDirty=false;_ttLocked=true;_ttDisarm();
    _ttFilterSaved();_ttRender();_ttRenderSaved();
    _ttSay("Saved “"+name+"”.");})
  .catch(function(){_ttSay("Devserver not reachable. Run venv/bin/python utilities/devserver.py");});}

function _ttDelete(id){
  var f=_ttFind(id);
  if(!f)return;
  if(id===_ttJid&&_ttGuard())return;
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
    if(_ttGuard())return;
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
  if(!p||_ttGuard())return;
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

_ttEl("tt-lock-btn").addEventListener("click",_ttToggleLock);
_ttEl("tt-save-btn").addEventListener("click",function(){_ttSave(false);});
_ttEl("tt-saveas-btn").addEventListener("click",function(){_ttSave(true);});
_ttEl("tt-clear-btn").addEventListener("click",_ttClear);

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
        'if(_wsSavedTab==="add-point"||_wsSavedTab==="edit-coords")_wsSavedTab="inspector";\n'
        'var _activeTab=_wsSavedTab||"inspector";\n'
        + _WS_MODE_JS

        # -- Display layers: location types, routes, journeys --
        # The shared control owns every filter on those layers (_dispApply);
        # _dispExtra adds the Workshop's own conditions to it.
        + map_style.display_controls_js("sessionStorage", "_wsDisp") +
        'var _dispPreview=false;\n'
        'try{_dispPreview=sessionStorage.getItem("_wsPreview")==="1";}catch(_e){}\n'
        'function _dispExtra(lyr){'
        'var x=[],jr=lyr==="journeys"||lyr==="journeys-hit";'
        'if(_dispPreview){'
        'if(lyr in _tierCats)x.push(["!=",["get","visibility"],"gm_secrets"]);'
        'else if(lyr==="routes"||jr)x.push(["==",["get","_playerVisible"],true]);}'
        'if(jr)x.push(["!=",["get","id"],_ttJid||""]);'
        'return x.length?x:null;}\n'

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
        '_activeTab=tab;_wsSetMode("tab",tab);'
        'document.querySelectorAll(".tab-btn,.nav-item[data-tab]").forEach(function(b){'
        'var on=b.dataset.tab===tab;b.classList.toggle("active",on);'
        'if(b.classList.contains("nav-item")){if(on)b.setAttribute("aria-current","page");'
        'else b.removeAttribute("aria-current");}});'
        'document.querySelectorAll(".panel").forEach(function(p){'
        'p.classList.toggle("active",p.id==="panel-"+tab);});'
        # Clear Tab 2 highlights when switching away
        'if(tab!=="route-index")_clearHighlights();'
        'if(tab!=="inspector"&&window._msClear)window._msClear();'
        'if(tab!=="travel-time"&&typeof _ttRelock==="function")_ttRelock();'
        '}\n'
        'document.querySelectorAll(".tab-btn").forEach(function(b){'
        'b.addEventListener("click",function(){_setTab(b.dataset.tab);});});\n'
        # Apply the restored (or default) tab now that _setTab exists — the
        # server-rendered HTML always marks "Add Point" active by default.
        '_setTab(_activeTab);\n'
        # -- Shell: hide/show, drag-resize, collapsible sections --
        'var _VIS_HTML='+json.dumps({k:_vis_icon(k) for k in _VIS_LABEL})+';\n'
        'var _SB_W="_wsSbW",_SB_H="_wsSbHidden",_SB_COL="_wsCollapsed";\n'
        'function _lsGet(k){try{return localStorage.getItem(k);}catch(e){return null;}}\n'
        'function _lsSet(k,v){try{localStorage.setItem(k,v);}catch(e){}}\n'
        'var _appEl=document.getElementById("app");\n'
        'function _sbWidth(w){'
        'w=Math.max(340,Math.min(w,window.innerWidth*0.7));'
        'document.documentElement.style.setProperty("--sb-w",Math.round(w)+"px");return w;}\n'
        'function _sbDock(h){'
        'var sh=document.getElementById("ws-subheader");'
        'if(h)document.getElementById("sb-float").appendChild(sh);'
        'else document.getElementById("sidebar-header").insertBefore(sh,document.getElementById("tab-bar"));}\n'
        'function _sbHide(h){'
        '_appEl.classList.toggle("sb-hidden",h);_lsSet(_SB_H,h?"1":"0");_sbDock(h);'
        'setTimeout(function(){map.resize();},0);}\n'
        'var _w0=parseFloat(_lsGet(_SB_W));if(_w0>0)_sbWidth(_w0);\n'
        'if(_lsGet(_SB_H)==="1"){_appEl.classList.add("sb-hidden");_sbDock(true);}\n'
        # -- Nav rail (#355): _wsNav rail|tabs and _wsNavPin, both persisted --
        'var _NAV="_wsNav",_NAVPIN="_wsNavPin";\n'
        'var _railEl=document.getElementById("nav-rail"),_navTouch=false;\n'
        'function _navMode(m){_appEl.classList.toggle("nav-tabs",m==="tabs");_lsSet(_NAV,m);'
        'setTimeout(function(){map.resize();},0);}\n'
        'function _navPin(p){_appEl.classList.toggle("nav-pinned",p);_lsSet(_NAVPIN,p?"1":"0");'
        'var b=document.getElementById("nav-pin");b.setAttribute("aria-pressed",p?"true":"false");'
        'var t=p?"Unpin the rail":"Pin the rail open";b.title=t;b.setAttribute("aria-label",t);'
        'b.querySelector(".nav-label").textContent=p?"Unpin":"Pin open";}\n'
        'if(_lsGet(_NAV)==="tabs")_appEl.classList.add("nav-tabs");\n'
        'if(window.ResizeObserver)new ResizeObserver(function(){'
        '_appEl.classList.toggle("nav-narrow",document.getElementById("sidebar").offsetWidth<440);'
        '}).observe(document.getElementById("sidebar"));\n'
        'if(_lsGet(_NAVPIN)==="1")_navPin(true);\n'
        'document.getElementById("nav-to-tabs").addEventListener("click",function(){_navMode("tabs");});\n'
        'document.getElementById("nav-to-rail").addEventListener("click",function(){_navMode("rail");});\n'
        'document.getElementById("nav-pin").addEventListener("click",function(){'
        '_navPin(!_appEl.classList.contains("nav-pinned"));});\n'
        'document.addEventListener("pointerdown",function(e){'
        '_navTouch=e.pointerType==="touch";'
        'if(!_railEl.contains(e.target))_railEl.classList.remove("open");});\n'
        'document.querySelectorAll(".nav-item[data-tab]").forEach(function(b){'
        'b.addEventListener("click",function(e){'
        'if(_navTouch&&!_railEl.classList.contains("open")&&!_appEl.classList.contains("nav-pinned")){'
        '_railEl.classList.add("open");e.preventDefault();return;}'
        '_railEl.classList.remove("open");_setTab(b.dataset.tab);});});\n'
        '_railEl.addEventListener("keydown",function(e){'
        'var d=e.key==="ArrowDown"?1:e.key==="ArrowUp"?-1:0;if(!d)return;e.preventDefault();'
        'var bs=[].slice.call(_railEl.querySelectorAll("button"));var i=bs.indexOf(document.activeElement);'
        'bs[(i+d+bs.length)%bs.length].focus();});\n'
        'document.addEventListener("click",function(e){var b=e.target.closest(".info-btn");if(!b)return;'
        'var t=document.getElementById(b.getAttribute("aria-controls"));var o=t.hidden;t.hidden=!o;b.setAttribute("aria-expanded",o?"true":"false");});\n'
        'document.addEventListener("keydown",function(e){if(e.key!=="Escape")return;'
        'document.querySelectorAll(".info-btn[aria-expanded=true]").forEach(function(b){b.click();});});\n'
        'document.getElementById("sb-toggle").addEventListener("click",function(){_sbHide(true);});\n'
        'document.getElementById("sb-show").addEventListener("click",function(){_sbHide(false);});\n'
        'document.addEventListener("keydown",function(e){'
        'if(e.key!=="\\\\"||e.ctrlKey||e.metaKey||e.altKey)return;'
        'var t=e.target;if(t&&(t.isContentEditable||/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)))return;'
        'e.preventDefault();_sbHide(!_appEl.classList.contains("sb-hidden"));});\n'
        '(function(){'
        'var rz=document.getElementById("sb-resizer"),sb=document.getElementById("sidebar");\n'
        'rz.addEventListener("pointerdown",function(e){'
        'rz.setPointerCapture(e.pointerId);rz.classList.add("drag");e.preventDefault();});\n'
        'rz.addEventListener("pointermove",function(e){'
        'if(!rz.classList.contains("drag"))return;_sbWidth(e.clientX-sb.getBoundingClientRect().left);});\n'
        'function end(){if(!rz.classList.contains("drag"))return;rz.classList.remove("drag");'
        '_lsSet(_SB_W,String(Math.round(sb.getBoundingClientRect().width)));map.resize();}\n'
        'rz.addEventListener("pointerup",end);rz.addEventListener("pointercancel",end);\n'
        'rz.addEventListener("dblclick",function(){'
        'document.documentElement.style.removeProperty("--sb-w");_lsSet(_SB_W,"");map.resize();});\n'
        'rz.addEventListener("keydown",function(e){'
        'var d=e.key==="ArrowLeft"?-24:e.key==="ArrowRight"?24:0;if(!d)return;e.preventDefault();'
        '_lsSet(_SB_W,String(Math.round(_sbWidth(sb.getBoundingClientRect().width+d))));map.resize();});'
        '})();\n'
        'function _secKey(h){return (h.closest(".panel")||{}).id+"|"+h.textContent.replace(/[(\\d].*$/,"").trim();}\n'
        'function _secApply(h,collapsed){'
        'h.classList.toggle("sec-collapsed",collapsed);h.setAttribute("aria-expanded",collapsed?"false":"true");'
        'for(var n=h.nextElementSibling;n&&!n.hasAttribute("data-collapsible");n=n.nextElementSibling)'
        'n.classList.toggle("sec-hide",collapsed);}\n'
        'var _secState={};try{_secState=JSON.parse(_lsGet(_SB_COL)||"{}")||{};}catch(e){}\n'
        'document.querySelectorAll("[data-collapsible]").forEach(function(h){'
        'h.tabIndex=0;h.setAttribute("role","button");var k=_secKey(h);_secApply(h,!!_secState[k]);'
        'function tog(){var c=!h.classList.contains("sec-collapsed");_secApply(h,c);'
        'if(c)_secState[k]=1;else delete _secState[k];_lsSet(_SB_COL,JSON.stringify(_secState));}\n'
        'h.addEventListener("click",tog);'
        'h.addEventListener("keydown",function(e){if(e.key==="Enter"||e.key===" "){e.preventDefault();tog();}});});\n'

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

        # Basemap triangle markers: all hidden except "Peak labels", which the
        # Layers menu toggles (wired below)
        + map_style.basemap_hide_js(map_style.BASEMAP_HIDDEN_LAYERS) +

        # Raster overlays — hidden by default, sit below all custom data
        map_style.raster_overlays_js(maptiler_key) +

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
        'if(_wsMode==="place"||window._wsJustPlaced)return;'
        'var f=e.features[0];'
        'if(!_showRoutePanel(f))return;'
        'map.getSource("route-selected").setData({type:"FeatureCollection",features:[f]});'
        '});\n'
        'map.on("click",function(e){'
        'var _onPin=map.queryRenderedFeatures(e.point,{layers:_locLayerIds||[]}).length;'
        'var _onRt=map.queryRenderedFeatures(e.point,{layers:["routes"]}).length;'
        'var _idle=(_wsMode==="select"||_activeTab==="travel-time"&&_wsMode!=="place")&&!window._wsJustPlaced;'
        'var _jh=(!_onPin&&_idle&&(_activeTab!=="travel-time"||(!_onRt&&(_ttLocked||!_ttStops.length))))?'
        'map.queryRenderedFeatures(e.point,{layers:["journeys-hit"]}):[];'
        'if(_jh.length&&_ttFind(_jh[0].properties.id)){'
        'if(_activeTab!=="travel-time"){'
        'if(_efSlug!==null||_efDirty()){if(!_efConfirmDiscard())return;_efReset();}'
        '_setTab("travel-time");}'
        '_ttLoad(_jh[0].properties.id);}'
        'else if(_activeTab==="travel-time"&&!_onPin)_ttSetPt(e.lngLat.lng,e.lngLat.lat,null);'
        'if(!map.queryRenderedFeatures(e.point,{layers:["routes"]}).length){'
        'if(map.getSource("route-selected")){'
        'map.getSource("route-selected").setData({type:"FeatureCollection",features:[]});}'
        '_hideRoutePanel();}'
        '});\n'

        # Icons + location symbol layers
        + icons_js +
        '_dispIcons();\n'
        'map.addSource("locations",{type:"geojson",data:_locGJ});\n'

        # icon_match expression + six-tier location layers (shared with the player map)
        + map_style.location_tiers_js() +

        # Highlight source/layer for Tab 2 selected markers
        'map.addSource("highlight-source",{type:"geojson",data:{type:"FeatureCollection",features:[]}});\n'
        'map.addLayer({id:"highlight-circles",type:"circle",source:"highlight-source",'
        'paint:{"circle-radius":16,"circle-color":"rgba(0,0,0,0)",'
        '"circle-stroke-width":3,"circle-stroke-color":"#f5d060","circle-stroke-opacity":0.9}});\n'

        # Selection rings: gold = in the multi-selection (see _msUpdateRings)
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
        # One action for a location, whether the pin or its search result was clicked
        'window._wsPinAction=function(feature,ev){'
        'var p=feature.properties;'
        'var slug=p._slug||p.slug||"";'
        'if(_wsMode==="place"||window._wsJustPlaced)return;'
        'if(_wsMode==="route"){if(slug)_addToQueue(slug);return;}'
        'if(_activeTab==="travel-time"&&!(_ttJid&&_ttLocked)){'
        'var coords=feature.geometry.coordinates;'
        'var name=p.title||p.label||slug||"";'
        '_ttSetPt(coords[0],coords[1],name,slug);return;}'
        'if(!slug)return;'
        'if(ev&&(ev.shiftKey||ev.ctrlKey||ev.metaKey)&&_activeTab==="inspector"){_msToggle(slug);return;}'
        'if(_msSel.length)window._msClear();'
        'if(!_ttStepAside())return;'
        '_openFieldEditor(feature);'
        '};\n'
        '_locLayerIds.forEach(function(lyr){'
        'map.on("click",lyr,function(e){'
        '_wsPinAction(e.features[0],e.originalEvent);'
        '});});\n'

        # Overlay toggle + opacity wiring (sessionStorage-persisted). The GM owns the
        # overlays: what the players see is each overlay's on/opacity, published to
        # the devserver, where "on" also needs the overlay's Share box ticked.
        'var _ovPub={},_ovTimer=null;\n'
        'function _pubOverlays(){'
        'clearTimeout(_ovTimer);'
        'var body={};'
        'Object.keys(_ovPub).forEach(function(k){body[k]=_ovPub[k]();});'
        'try{fetch("/api/map-overlays",{method:"POST",'
        'headers:{"Content-Type":"application/json"},body:JSON.stringify(body)})'
        '.catch(function(){});}catch(_e){}}\n'
        'function _wireOverlay(key,layerId,ssOn,ssOp,ssShare){'
        'var tog=document.getElementById(key+"-toggle"),opc=document.getElementById(key+"-opacity"),'
        'shr=document.getElementById(key+"-share");'
        'try{'
        'var sv=sessionStorage.getItem(ssOn),so=sessionStorage.getItem(ssOp);'
        'if(sv==="1"){tog.checked=true;map.setLayoutProperty(layerId,"visibility","visible");}'
        'if(so!=null){opc.value=so;map.setPaintProperty(layerId,"raster-opacity",parseFloat(so)/100);}'
        'shr.checked=sessionStorage.getItem(ssShare)==="1";'
        '}catch(e){}'
        '_ovPub[key]=function(){return{on:tog.checked&&shr.checked,opacity:parseInt(opc.value)/100};};'
        'tog.addEventListener("change",function(){'
        'map.setLayoutProperty(layerId,"visibility",tog.checked?"visible":"none");'
        'try{sessionStorage.setItem(ssOn,tog.checked?"1":"0");}catch(e){}'
        '_pubOverlays();});'
        'shr.addEventListener("change",function(){'
        'try{sessionStorage.setItem(ssShare,shr.checked?"1":"0");}catch(e){}'
        '_pubOverlays();});'
        'opc.addEventListener("input",function(){'
        'map.setPaintProperty(layerId,"raster-opacity",parseInt(opc.value)/100);'
        'try{sessionStorage.setItem(ssOp,opc.value);}catch(e){}'
        'clearTimeout(_ovTimer);_ovTimer=setTimeout(_pubOverlays,250);});}\n'
        '_wireOverlay("topo","topo-overlay","_wsTopoOn","_wsTopoOp","_wsTopoShare");'
        '_wireOverlay("sat","sat-overlay","_wsSatOn","_wsSatOp","_wsSatShare");'
        '_pubOverlays();\n'

        # Peak markers: the basemap's "Peak labels" layer, shown by default,
        # sessionStorage-persisted. The player map always hides it.
        '(function(){'
        'var cb=document.getElementById("peak-toggle"),pid='
        + json.dumps(map_style.BASEMAP_PEAK_LAYER) +
        ';'
        'try{if(sessionStorage.getItem("_wsPeaks")==="0")cb.checked=false;}catch(e){}'
        'function apply(){if(map.getLayer(pid))'
        'map.setLayoutProperty(pid,"visibility",cb.checked?"visible":"none");}'
        'apply();'
        'cb.addEventListener("change",function(){apply();'
        'try{sessionStorage.setItem("_wsPeaks",cb.checked?"1":"0");}catch(e){}});'
        '})();\n'

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
        '_showOverlayErr(tid,status);'
        '_pubOverlays();});\n'

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

        # Player's-eye preview switch, then apply the saved display state and the
        # preview once the layers exist
        '(function(){'
        'var cb=document.getElementById("preview-toggle");cb.checked=_dispPreview;'
        'cb.addEventListener("change",function(){'
        '_dispPreview=cb.checked;'
        'try{sessionStorage.setItem("_wsPreview",cb.checked?"1":"0");}catch(_e){}'
        '_dispApply();});'
        '})();\n'
        '_dispApply();\n'

        # Travel tab working journey: one dashed LineString per leg
        'map.addSource("tt-line",{type:"geojson",data:{type:"FeatureCollection",features:[]}});\n'
        'map.addLayer({id:"tt-line-layer",type:"line",source:"tt-line",'
        'layout:{"line-cap":"round","line-join":"round"},'
        'paint:{"line-color":"#e8a060","line-width":2.5,"line-opacity":0.9,"line-dasharray":[4,3]}});\n'

        'map.addControl(new maplibregl.ScaleControl({maxWidth:100,unit:"metric"}),"bottom-left");\n'

        '});\n'  # end map.on('load')

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
        'if(!_showRoutePanel(feat))return;'
        'map.getSource("route-selected").setData({type:"FeatureCollection",features:[feat]});'
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
        'if(_efSlug!==null||_efDirty()){if(!_efConfirmDiscard())return false;_efReset();}'
        'if(!_ttStepAside())return false;'
        '_selectedRouteId=feature.id||feature.properties._route_id||"";'
        '_refreshRoutePanel();'
        'document.getElementById("route-panel").hidden=false;'
        'document.body.classList.add("rt-selected");'
        'if(_activeTab!=="inspector")_setTab("inspector");'
        'return true;'
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
        'cells[3].innerHTML=_fmtHours(_routeHours(f),approx)+\' <span class="ri-mode">\'+_TT.speeds[m].label+\'</span>\';'
        'var pv=f.properties._playerVisible,pub=f.properties.visibility==="public";'
        'cells[4].innerHTML=pv?_VIS_HTML.pub:(pub?_VIS_HTML.held:_VIS_HTML.gm);'
        '}\n'
        'document.getElementById("route-panel-vis").addEventListener("change",function(){_patchRoute("visibility",this.value);});\n'
        'document.getElementById("route-panel-mode").addEventListener("change",function(){_patchRoute("mode",this.value);});\n'
        'function _hideRoutePanel(){'
        '_selectedRouteId=null;'
        'document.getElementById("route-panel").hidden=true;'
        'document.body.classList.remove("rt-selected");'
        'if(map.getSource("route-selected"))map.getSource("route-selected").setData({type:"FeatureCollection",features:[]});'
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
        'var _pendingEdits={};\n'
        'var _dragMarker=null;\n'
        'var _editBadge=document.getElementById("edit-badge");'
        'var _railBadge=document.getElementById("edit-badge-rail");'
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
        '+\'<button id="ec-save" style="padding:4px 12px;background:#1a2a0a;border:1px solid #6a9a2c;color:#a8d840;font-size:var(--fs-2);cursor:pointer;border-radius:2px;">Save</button>\''
        '+\'<button id="ec-cancel" style="padding:4px 10px;background:#2a1e08;border:1px solid rgba(184,146,44,0.3);color:#9a8a6a;font-size:var(--fs-2);cursor:pointer;border-radius:2px;">Cancel</button>\''
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
        'if(_efSlug===slug){_efLat.value=lat.toFixed(6);_efLon.value=lon.toFixed(6);_efCurrentCoords={lng:lon,lat:lat};}'
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
        'if(count===0){_editBadge.classList.add("hidden");_railBadge.classList.add("hidden");_unsavedSection.classList.add("hidden");return;}'
        '_editBadge.textContent=count;_editBadge.classList.remove("hidden");'
        '_railBadge.textContent=count;_railBadge.classList.remove("hidden");'
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
        'var _efBase=null;\n'
        'var _efCurrentCoords=null;\n'
        'var _pendingFieldEdits={};\n'
        'var _efSlugEl=document.getElementById("ef-slug");\n'
        'var _efName=document.getElementById("ef-name");\n'
        'var _efFantasy=document.getElementById("ef-fantasy");\n'
        'var _efType=document.getElementById("ef-type");\n'
        'var _efIcon=document.getElementById("ef-icon");\n'
        'var _efIconNote=document.getElementById("ef-icon-note");\n'
        'var _efOpenCat="";\n'
        'var _efTypeIcons=' + json.dumps({k: v.removeprefix("cat-") for k, v in type_icons().items()}) + ';\n'
        'var _efStatus=document.getElementById("ef-status");\n'
        'var _efSaveBtn=document.getElementById("ef-save-btn");\n'
        'var _efMoveBtn=document.getElementById("ef-move-btn");\n'
        'var _efLat=document.getElementById("ef-lat");\n'
        'var _efLon=document.getElementById("ef-lon");\n'
        'var _efModeEl=document.getElementById("ef-mode");\n'
        'var _efCloseBtn=document.getElementById("ef-close-btn");\n'
        'var _efRegion=document.getElementById("ef-region");\n'
        'var _efDesc=document.getElementById("ef-desc");\n'
        'var _efAdv=document.getElementById("ef-adv");\n'
        'var _efAdvStatus=document.getElementById("ef-adv-status");\n'
        'var _efAdvScalars=document.getElementById("ef-adv-scalars");\n'
        'var _efAdvReadonly=document.getElementById("ef-adv-readonly");\n'
        'var _efAdvBase=null;\n'
        'var _efAdvBad=null;\n'
        'var _efTypePlaceholder=_efType.querySelector(\'option[value=""]\');\n'
        'var _efCreateOnly=document.querySelectorAll(".ef-create-only");\n'
        'var _efEditOnly=document.querySelectorAll(".ef-edit-only");\n'

        + _EF_DIFF_JS + _EF_ICON_NOTE_JS
        + _INSPECTOR_JS +

        # Promise-returning PATCH shared by the field editor and the batch bar.
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

        'function _patchFrontmatter(slug,fields,onOk){'
        '_efStatus.textContent="Saving…";_efStatus.className="hint";'
        '_patchFrontmatterRaw(slug,fields)'
        '.then(function(data){'
        'if(data.ok){'
        '_efStatus.textContent="✓ Saved";_efStatus.className="hint ok";'
        'if(fields.visibility)_refreshLocSource();'
        'if(onOk)onOk();'
        '}else{_efStatus.textContent="✗ "+(data.error||"error");_efStatus.className="hint err";}'
        '})'
        '.catch(function(){_efStatus.textContent="✗ Network error";_efStatus.className="hint err";});'
        '}\n'

        + _INSPECTOR_WIRE_JS

        # -- Multi-select and the batch bar --
        + _MULTISELECT_JS +

        # -- Search / find-location widget --
        _WS_LATLON_JS +
        'var _wsSearch=document.getElementById("ws-search");'
        'var _wsSearchDrop=document.getElementById("ws-search-drop");'
        'var _wsSearchGroups=['
        '{lbl:"Major",cats:["city","capital","bridge","landmark","fortress"]},'
        '{lbl:"Towns",cats:["town","village"]},'
        '{lbl:"Sacred",cats:["sacred-site","power-site"]},'
        '{lbl:"Terrain",cats:["oasis","lake","water-body"]},'
        '{lbl:"Routes",cats:["route-node","caravanserai","chokepoint","mountain-pass"]},'
        '{lbl:"Other",cats:["ruins","poi","site","dungeon"]}'
        '];\n'

        'function _wsFlyTo(item){'
        'if(item&&item.lat!=null&&item.lon!=null){'
        'map.flyTo({center:[item.lon,item.lat],zoom:Math.max(map.getZoom(),8),duration:600});}'
        '_wsSearchDrop.hidden=true;_wsSearch.blur();}\n'

        # Picking a result is clicking its pin: the active tab decides what that does
        'function _wsPick(item){'
        '_wsFlyTo(item);'
        'if(!item)return;'
        '_wsPinAction({properties:{slug:item.slug,title:item.title,label:item.label,'
        'category:item.category,mapMarker:item.mapMarker,visibility:item.visibility},'
        'geometry:{coordinates:[item.lon,item.lat]}});}\n'

        'var _wsGoMarker=null;\n'
        'function _wsGoTo(ll){'
        'if(_wsGoMarker)_wsGoMarker.remove();'
        '_wsGoMarker=new maplibregl.Marker({color:"#b8922c"}).setLngLat([ll.lon,ll.lat]).addTo(map);'
        '_wsFlyTo({lat:ll.lat,lon:ll.lon});}\n'

        'function _wsRender(q){'
        'q=(q||"").trim().toLowerCase();'
        'var html="",total=0;'
        'var ll=_wsParseLatLon(q);'
        'if(ll){html+=\'<div class="wsd-group">Coordinates</div><div class="wsd-item" data-ll="\'+ll.lat+\',\'+ll.lon+\'">Go to \'+ll.lat+\', \'+ll.lon+\'</div>\';total++;}'
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
        'if(el.dataset.ll){var c=el.dataset.ll.split(",");_wsGoTo({lat:+c[0],lon:+c[1]});return;}'
        '_wsPick(_locBySlug[el.dataset.slug]);});});}\n'

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

    region_options = "\n".join(
        f'<option value="{r["slug"]}">{r["title"]}</option>' for r in region_names
    )
    mode_options = "".join(
        f'<option value="{m}">{spec["label"]} ({spec["kmpd"]} km/d)</option>'
        for m, spec in travel_time.SPEEDS.items()
    )

    panel_inspector = _build_panel_inspector(region_options)
    panel_route = _build_panel_plan_route()
    panel_travel = _build_panel_travel_time()
    panel_batch = _build_panel_batch()
    app_js = _build_app_js(style_url, icons_js, maptiler_key=maptiler_key)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        "<title>Map Workshop — Tarim-Shaïal</title>\n"
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/maplibre-gl@5/dist/maplibre-gl.css">\n'
        "<style>\n" + _CSS + map_style.display_controls_css() + map_style.popup_css() + "</style>\n"
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
        '<button id="sb-toggle" type="button" title="Hide sidebar (\\)" aria-label="Hide sidebar">◀</button>'
        '</div>\n'
        '      <div id="ws-subheader">\n'
        '        <button id="layers-btn">⊞ Layers</button>\n'
        '        <div id="layers-dropdown" hidden>\n'
        '          <label><input type="checkbox" id="topo-toggle"> Topo overlay\n'
        '            <input type="range" id="topo-opacity" min="0" max="100" value="55" title="Opacity"></label>\n'
        '          <label class="ov-share"><input type="checkbox" id="topo-share"> Share with players</label>\n'
        '          <label><input type="checkbox" id="sat-toggle"> Satellite Plain\n'
        '            <input type="range" id="sat-opacity" min="0" max="100" value="60" title="Opacity"></label>\n'
        '          <label class="ov-share"><input type="checkbox" id="sat-share"> Share with players</label>\n'
        '          <hr>\n'
        + map_style.display_layer_rows_html("Saved journeys") +
        '          <label><input type="checkbox" id="peak-toggle" checked> Peak markers</label>\n'
        '          <hr>\n'
        + map_style.display_type_grid_html() +
        '          <hr>\n'
        '          <label title="Hide what the player map would not show: GM-only locations, routes and journeys">'
        '<input type="checkbox" id="preview-toggle"> Player\'s-eye preview</label>\n'
        '        </div>\n'
        '        <span id="ws-zoom">zoom <span id="ws-zoom-val">—</span></span>\n'
        '      </div>\n'
        '      <div id="ws-search-row">\n'
        '        <div id="ws-search-wrap">\n'
        '          <span id="ws-search-icon">⌕</span>\n'
        '          <input id="ws-search" type="text" placeholder="Find location…" autocomplete="off" spellcheck="false">\n'
        '          <div id="ws-search-drop" hidden></div>\n'
        '        </div>\n'
        '      </div>\n'
        '      <div id="tab-bar">\n'
        + _tab_buttons_html() +
        "      </div>\n"
        "    </div>\n"
        '    <div id="sb-main">\n'
        + _nav_rail_html() +
        '    <div id="sb-panels">\n'
        '    <div id="panel-inspector" class="panel active">\n'
        + panel_batch
        + '<div id="insp-single">\n'
        + panel_inspector
        + "\n    </div>\n"
        '<div id="route-panel" hidden>\n'
        '  <div class="rp-head"><h2 class="rp-title list-heading">Editing route</h2>'
        '<button id="route-panel-close" type="button" class="close-x" title="Close (Esc)" aria-label="Close">✕</button></div>\n'
        '  <div id="route-panel-label"></div>\n'
        '  <div id="route-panel-time"></div>\n'
        '  <div id="route-panel-seen"></div>\n'
        '  <div class="rp-row"><label for="route-panel-vis">Visibility</label>'
        '<select id="route-panel-vis"><option value="gm_secrets">GM only</option>'
        '<option value="public">Public</option></select></div>\n'
        f'  <div class="rp-row"><label for="route-panel-mode">Travel by</label>'
        f'<select id="route-panel-mode">{mode_options}</select></div>\n'
        '  <div class="btn-row"><button id="route-panel-regenerate" class="btn btn-sm">🔄 Regenerate</button>'
        '<button id="route-panel-delete" class="btn btn-sm btn-danger">🗑 Delete Route</button></div>\n'
        '</div>\n'
        '    </div>\n'
        '    <div id="panel-route-index" class="panel">\n'
        '<h3 data-collapsible>Add route</h3>\n'
        + panel_route
        + '\n<h3 data-collapsible>Routes</h3>\n'
        + route_index_html
        + "\n    </div>\n"
        '    <div id="panel-travel-time" class="panel">\n'
        + panel_travel
        + "\n    </div>\n"
        '    </div>\n'
        '    </div>\n'
        '    <div id="player-share" style="display:none">\n'
        '      <span style="color:#8ad08a;font-size:var(--fs-2);white-space:nowrap;">📡 Players:</span>\n'
        '      <a id="player-share-link" href="#" target="_blank" style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;"></a>\n'
        '      <button id="player-share-copy" title="Copy link">⎘</button>\n'
        '    </div>\n'
        "  </div>\n"
        '  <div id="sb-resizer" role="separator" aria-orientation="vertical" tabindex="0" '
        'title="Drag to resize (double-click to reset)"></div>\n'
        '  <div id="sb-float"><button id="sb-show" type="button" title="Show sidebar (\\)">▶ Sidebar</button></div>\n'
        '  <div id="map"></div>\n'
        '  <div id="ws-mode-chip" role="status" hidden><span id="ws-mode-label"></span>'
        '<button id="ws-mode-cancel" type="button" title="Back to Select (Esc)">Esc</button></div>\n'
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

# Start view when there is neither a GM position nor a stored view. The Workshop
# opens on [75, 40] zoom 5; this default predates the start-view order and is
# left as it was (#324 changes when the view is chosen, not what the default is).
PLAYER_DEFAULT_VIEW = {"lng": 70, "lat": 40, "zoom": 4}
PLAYER_VIEW_KEY = "ts_player_view"
# The player's own layer choices (location types, routes, journeys), per browser.
PLAYER_DISPLAY_KEY = "ts_player_display"
PLAYER_GM_VIEW_TIMEOUT_MS = 800
# Zoom range a GM or stored view is clamped to; the same as the Workshop map's.
PLAYER_VIEW_ZOOM_RANGE = (3, 18)

# Chooses the first view before the map is constructed, so a refresh never shows
# the default and then eases to the GM. Order: GM position (GET /api/map-center,
# short timeout), last view stored on this device, default. Every storage access
# is guarded; the page must work with storage blocked.
_PLAYER_VIEW_JS = r"""
function _cleanView(v){
  if(!v||typeof v!=='object')return null;
  var lng=v.lng,lat=v.lat,zoom=v.zoom;
  if(typeof lng!=='number'||typeof lat!=='number'||typeof zoom!=='number')return null;
  if(!isFinite(lng)||!isFinite(lat)||!isFinite(zoom)||Math.abs(lng)>180)return null;
  return{lng:lng,lat:Math.max(-85,Math.min(85,lat)),zoom:Math.max(_MIN_ZOOM,Math.min(_MAX_ZOOM,zoom))};
}
function _viewKey(d){
  return d.lng.toFixed(5)+','+d.lat.toFixed(5)+(d.zoom!=null?','+d.zoom.toFixed(2):'');
}
function _storedView(){
  try{return _cleanView(JSON.parse(localStorage.getItem(_VIEW_KEY)));}catch(e){return null;}
}
function _storeView(){
  if(!map)return;
  try{
    var c=map.getCenter();
    localStorage.setItem(_VIEW_KEY,JSON.stringify({lng:c.lng,lat:c.lat,zoom:map.getZoom()}));
  }catch(e){}
}
function _chooseStart(gm){
  if(_cleanView(gm))return{view:_cleanView(gm),gm:gm};
  return{view:_storedView()||_DEFAULT_VIEW,gm:null};
}
function _fetchGmView(cb){
  var done=false,ctrl=typeof AbortController==='function'?new AbortController():null;
  function finish(d){if(done)return;done=true;clearTimeout(timer);cb(d);}
  var timer=setTimeout(function(){finish(null);if(ctrl)ctrl.abort();},_GM_VIEW_TIMEOUT);
  try{
    fetch('/api/map-center',ctrl?{signal:ctrl.signal}:undefined)
    .then(function(r){return r.json();})
    .then(finish)
    .catch(function(){finish(null);});
  }catch(e){finish(null);}
}
"""


# The GM's raster overlays on the player map. The player cannot change them: the
# devserver relays the Workshop's on/opacity (GET /api/map-overlays) and this polls
# it, independently of Follow GM. A failed poll keeps the last state (hidden before
# the first answer); an overlay whose tiles fail stays hidden, silently, until the
# GM turns it off and on again.
_PLAYER_OVERLAY_JS = """\
var _overlayFailed = {};
var _overlayTimer = null;
function _applyOverlays(d){
  Object.keys(_OVERLAYS).forEach(function(k){
    var id = _OVERLAYS[k];
    if(!map || !map.getLayer(id))return;
    var o = d && typeof d === 'object' ? d[k] : null;
    var want = !!(o && o.on === true);
    if(!want)_overlayFailed[k] = false;
    map.setLayoutProperty(id, 'visibility', want && !_overlayFailed[k] ? 'visible' : 'none');
    if(o && typeof o.opacity === 'number' && isFinite(o.opacity))
      map.setPaintProperty(id, 'raster-opacity', Math.min(1, Math.max(0, o.opacity)));
  });
}
function _pollOverlays(){
  try{
    fetch('/api/map-overlays').then(function(r){return r.ok ? r.json() : null;})
    .then(function(d){if(d)_applyOverlays(d);}).catch(function(){});
  }catch(e){}
}
function _startOverlayPolling(){
  if(_overlayTimer)return;
  _pollOverlays();
  _overlayTimer = setInterval(_pollOverlays, 2000);
}
function _overlayError(e){
  var src = e && e.sourceId, hit = false;
  Object.keys(_OVERLAYS).forEach(function(k){
    if(_OVERLAYS[k] !== src)return;
    hit = true;
    _overlayFailed[k] = true;
    if(map.getLayer(src))map.setLayoutProperty(src, 'visibility', 'none');
  });
  if(!hit)console.error(e && e.error ? e.error : e);
}
"""


# Top-left, clear of the nav control (top-right), the scale bar (bottom-right) and
# the Follow GM button (bottom-centre). 44px targets throughout.
_PLAYER_LAYERS_CSS = """\
#layers-btn { position:fixed; z-index:100; top:calc(10px + env(safe-area-inset-top));
  left:calc(10px + env(safe-area-inset-left)); width:44px; height:44px; padding:0;
  background:rgba(26,18,8,0.85); color:#c8a84a; border:1px solid rgba(184,146,44,0.4);
  border-radius:8px; font-size:22px; line-height:1; cursor:pointer; touch-action:manipulation;
  backdrop-filter:blur(6px); }
#layers-btn[aria-expanded=true] { border-color:#b8922c; color:#e8dcc4; }
#layers-panel { position:fixed; z-index:100; top:calc(62px + env(safe-area-inset-top));
  left:calc(10px + env(safe-area-inset-left)); width:min(300px, calc(100vw - 80px));
  max-height:calc(100% - 150px - env(safe-area-inset-top) - env(safe-area-inset-bottom));
  overflow-y:auto; padding:12px; background:rgba(26,18,8,0.92); color:#e8dcc4;
  border:1px solid rgba(184,146,44,0.4); border-radius:8px; font-family:Georgia,serif;
  backdrop-filter:blur(6px); }
"""

_PLAYER_LAYERS_JS = """\
(function(){
  var btn = document.getElementById('layers-btn'), panel = document.getElementById('layers-panel');
  function setOpen(open){
    panel.hidden = !open;
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
  }
  btn.addEventListener('click', function(e){e.stopPropagation(); setOpen(panel.hidden);});
  document.addEventListener('click', function(e){
    if(!panel.hidden && !panel.contains(e.target))setOpen(false);
  });
})();
"""


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
        "var map = null;\n"
        f"var _VIEW_KEY = {json.dumps(PLAYER_VIEW_KEY)};\n"
        f"var _DEFAULT_VIEW = {json.dumps(PLAYER_DEFAULT_VIEW)};\n"
        f"var _MIN_ZOOM = {PLAYER_VIEW_ZOOM_RANGE[0]}, _MAX_ZOOM = {PLAYER_VIEW_ZOOM_RANGE[1]};\n"
        f"var _GM_VIEW_TIMEOUT = {PLAYER_GM_VIEW_TIMEOUT_MS};\n"
        + _PLAYER_VIEW_JS
        + map_style.display_controls_js("localStorage", PLAYER_DISPLAY_KEY)
        + f"var _OVERLAYS = {json.dumps(map_style.OVERLAY_LAYERS)};\n"
        + _PLAYER_OVERLAY_JS +
        # Use location.origin so that transformRequest returns absolute URLs.
        # MapLibre fetches vector tiles in a blob:-URL Worker; relative URLs cannot
        # be resolved in that context and silently fail, leaving all vector tile
        # sources (water, rivers, land colour) empty.
        "var _proxyBase=window.location.origin;\n"

        # The map is built from _initMap(), after the start view is chosen.
        "function _initMap(start){\n"
        "var v = start.view;\n"
        # The first poll must not re-ease to where the map already is.
        "_lastCenter = start.gm ? _viewKey(start.gm) : null;\n"
        f"map = new maplibregl.Map({{"
        f"container:'map',"
        f"style:_proxyBase+'{proxy_style_path}',"
        f"center:[v.lng,v.lat],zoom:v.zoom,"
        f"transformRequest:function(url,resourceType){{"
        f"if(url.indexOf('https://api.maptiler.com/')===0){{"
        f"return{{url:_proxyBase+'/api/maptiler-proxy?url='+encodeURIComponent(url)}};}}"
        f"}}"
        f"}});\n"

        "map.addControl(new maplibregl.NavigationControl(), 'top-right');\n"
        "map.addControl(new maplibregl.ScaleControl({maxWidth:100,unit:'metric'}), 'bottom-right');\n"

        # Remember the view on this device (debounced; not per move event).
        "var _viewTimer = null;\n"
        "map.on('moveend', function(){clearTimeout(_viewTimer);_viewTimer = setTimeout(_storeView, 400);});\n"

        "map.on('load', function() {\n"
        + map_style.basemap_hide_js(map_style.PLAYER_HIDDEN_LAYERS)
        + map_style.raster_overlays_js(maptiler_key)
        + icons_js
        + "_dispIcons();\n"
        # Same stacking as the Workshop: routes, then journeys, then the pins on top.
        "  map.addSource('routes', {type:'geojson', data: _routeGJ});\n"
        + map_style.routes_layer_js()
        + "\n"
        "  map.addSource('journeys', {type:'geojson', data: _journeyGJ});\n"
        + map_style.journeys_layer_js()
        + "\n"
        "  map.addSource('locations', {type:'geojson', data: _locGJ});\n"
        + map_style.location_tiers_js()
        + "\n"
        + map_style.hover_popup_js(gm_badge=False, tap_to_open=True)
        + "\n"
        + map_style.journey_hover_js(tap_to_open=True)
        + "\n"
        "  map.on('error', _overlayError);\n"
        "  _dispApply();\n"
        "  _startOverlayPolling();\n"
        "  _startPolling();\n"
        "});\n"
        "}\n"

        "function _startPolling(){\n"
        "  if(_pollTimer)return;\n"
        "  _pollTimer = setInterval(function(){\n"
        "    if(!_following)return;\n"
        "    fetch('/api/map-center').then(function(r){return r.json();})\n"
        "    .then(function(d){\n"
        "      if(d.lng==null||d.lat==null)return;\n"
        "      var key=_viewKey(d);\n"
        "      if(key===_lastCenter)return;\n"
        "      _lastCenter=key;\n"
        "      var easeOpts={center:[d.lng,d.lat],duration:400};\n"
        "      if(d.zoom!=null)easeOpts.zoom=d.zoom;\n"
        "      map.easeTo(easeOpts);\n"
        "    }).catch(function(){});\n"
        "  },2000);\n"
        "}\n"

        + _PLAYER_LAYERS_JS +
        "document.getElementById('follow-btn').addEventListener('click',function(){\n"
        "  _following=!_following;\n"
        "  this.textContent=_following?'● Following GM':'○ Follow GM';\n"
        "  this.classList.toggle('off',!_following);\n"
        "});\n"

        # Phones drop the page without beforeunload, so save on pagehide and when hidden.
        "window.addEventListener('pagehide', _storeView);\n"
        "document.addEventListener('visibilitychange', function(){\n"
        "  if(document.visibilityState==='hidden')_storeView();\n"
        "});\n"

        "_fetchGmView(function(gm){ _initMap(_chooseStart(gm)); });\n"
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
        + _PLAYER_LAYERS_CSS
        + map_style.display_controls_css(touch=True)
        + map_style.popup_css()
        + "</style>\n"
        "</head>\n"
        "<body>\n"
        '<div id="map"></div>\n'
        '<button id="follow-btn">● Following GM</button>\n'
        '<button id="layers-btn" aria-label="Layers" aria-expanded="false" aria-controls="layers-panel">⊞</button>\n'
        '<div id="layers-panel" hidden>\n'
        '<div class="it-heading">Map layers</div>\n'
        '<div class="disp-layers">\n'
        + map_style.display_layer_rows_html("Journeys")
        + "</div>\n"
        + map_style.display_type_grid_html()
        + "</div>\n"
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
