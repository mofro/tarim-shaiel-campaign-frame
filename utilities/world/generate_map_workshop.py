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
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
VAULT_ROOT = SCRIPT_DIR.parent.parent

sys.path.insert(0, str(SCRIPT_DIR.parent))

from locations.location_parser import load_all_locations
from locations.map_icons import icon_registration_js
from locations.location_components import MAPTILER_STYLE_URL, MAPTILER_KEY, MAPTILER_STYLE_ID

LOCATIONS_DIR = VAULT_ROOT / "world" / "locations"
ROUTES_PATH   = VAULT_ROOT / "world" / "data" / "tarim-shaiel-routes.geojson"
REGIONS_PATH  = VAULT_ROOT / "world" / "data" / "tarim-shaiel-regions.geojson"
OUTPUT_PATH   = VAULT_ROOT / "map-workshop.html"

CATEGORIES = [
    "city", "town", "caravanserai", "capital", "fortress", "sacred-site",
    "ruins", "route-node", "water-body", "landmark", "mythic-landscape",
]


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
        features.append({
            "type": "Feature",
            "id": f'location_{loc["slug"]}',
            "properties": {
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
            },
            "geometry": {
                "type": "Point",
                "coordinates": [loc["lon"], loc["lat"]],
            },
        })
    return {"type": "FeatureCollection", "features": features}


def _build_route_index(routes_geojson: dict) -> list:
    results = []
    pace = 30.0
    for feat in routes_geojson.get("features", []):
        fid = feat.get("id", "")
        props = feat.get("properties", {})
        coords = feat.get("geometry", {}).get("coordinates", [])
        label = props.get("label") or props.get("title") or fid
        kind = "spur" if fid.startswith("route_spur_") else "main"
        is_approx = len(coords) <= 2
        dist_km = path_length_km(coords) if len(coords) >= 2 else 0.0
        days = round(dist_km / pace, 1) if dist_km else 0.0
        results.append({
            "id": fid, "label": label, "kind": kind,
            "dist_km": round(dist_km, 0), "is_approx": is_approx, "days": days,
        })
    results.sort(key=lambda r: (r["kind"] != "main", r["id"]))
    return results


def _route_index_html(route_index: list) -> str:
    main_routes = [r for r in route_index if r["kind"] == "main"]
    spurs = [r for r in route_index if r["kind"] == "spur"]

    def row(r: dict) -> str:
        p = "~" if r["is_approx"] else ""
        d = f'{p}{int(r["dist_km"])} km'
        t = f'{p}{r["days"]:.0f} days'
        return f'<tr><td class="ri-id">{r["id"]}</td><td>{r["label"]}</td><td>{d}</td><td>{t}</td></tr>'

    def section(title: str, rows: list) -> str:
        if not rows:
            return ""
        thead = "<thead><tr><th>ID</th><th>Label</th><th>Distance</th><th>Travel (30 km/d)</th></tr></thead>"
        tbody = "<tbody>" + "".join(row(r) for r in rows) + "</tbody>"
        return f"<h3>{title}</h3><table>{thead}{tbody}</table>"

    note = '<p class="ri-note">~ = straight-line estimate (2-point segment, not road-routed)</p>'
    return (
        section("Main Routes", main_routes)
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
#app { display: flex; height: 100vh; }
#sidebar { min-width: 340px; display: flex; flex-direction: column;
  background: #120f08; border-right: 1px solid rgba(184,146,44,0.3); overflow: hidden; }
#sidebar-header { padding: 12px 14px 0; border-bottom: 1px solid rgba(184,146,44,0.2);
  flex-shrink: 0; }
#app-title { font-size: 13px; letter-spacing: 0.12em; text-transform: uppercase;
  color: #b8922c; margin-bottom: 10px; }
#tab-bar { display: flex; gap: 2px; }
.tab-btn { flex: 1; padding: 7px 4px; font-size: 11px; letter-spacing: 0.06em;
  text-transform: uppercase; background: #1a1410; border: 1px solid rgba(184,146,44,0.2);
  border-bottom: none; color: #8a7a60; cursor: pointer; border-radius: 3px 3px 0 0;
  transition: background 0.15s; }
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
/* Map */
#map { flex: 1; }
.maplibregl-map { font: inherit; }
.ts-popup { font-family: Georgia, serif; }
.ts-popup__title { font-size: 13px; font-weight: bold; color: #1a1208; }
.ts-popup__type { font-size: 11px; color: #6a5a3a; margin-top: 2px; }
.ts-map-popup .maplibregl-popup-content { background: #f5f0e8; padding: 8px 12px;
  border-radius: 3px; box-shadow: 0 2px 8px rgba(0,0,0,0.4); }
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
<button id="add-generate-btn" class="btn">Generate Command</button>
<div id="add-command-block" class="command-block hidden">
  <pre id="add-command-text"></pre>
  <button id="add-copy-btn" class="btn btn-sm">Copy to Clipboard</button>
</div>
<p class="hint">After running:<br>
<code>python utilities/build.py geojson</code><br>
then regenerate this workshop.</p>
"""


def _build_panel_plan_route() -> str:
    return """
<p class="hint" style="color:#7a6a50;">Click location markers on the map to add waypoints.</p>
<ul id="route-queue-list"><li class="queue-empty">No waypoints yet.</li></ul>
<div class="btn-row">
  <button id="route-remove-btn" class="btn btn-sm btn-danger" disabled>Remove Last</button>
  <button id="route-clear-btn" class="btn btn-sm btn-danger" disabled>Clear All</button>
</div>
<div class="field-group">
  <label style="flex-direction:row;align-items:center;gap:8px;cursor:pointer;">
    <input type="checkbox" id="route-spur-cb" style="accent-color:#b8922c;">
    Spur route (branch)
  </label>
</div>
<button id="route-generate-btn" class="btn" disabled>Generate Command</button>
<div id="route-command-block" class="command-block hidden">
  <pre id="route-command-text"></pre>
  <button id="route-copy-btn" class="btn btn-sm">Copy to Clipboard</button>
</div>
<p class="hint">After running:<br>
<code>python utilities/routes/generate_routes.py</code><br>
to snap to roads, then regenerate.</p>
"""


def _build_app_js(style_url: str, icons_js: str) -> str:
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

        # -- Active tab state --
        'var _activeTab="add-point";\n'

        # -- Map init --
        'var map=new maplibregl.Map({'
        'container:"map",'
        'style:"' + style_url + '",'
        'center:[75.0,40.0],'
        'zoom:5,'
        'minZoom:3,'
        'maxZoom:14'
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
        '}\n'
        'document.querySelectorAll(".tab-btn").forEach(function(b){'
        'b.addEventListener("click",function(){_setTab(b.dataset.tab);});});\n'

        # -- Tab 1: coordinate picker --
        'var _addLat=document.getElementById("add-lat");'
        'var _addLon=document.getElementById("add-lon");'
        'var _addName=document.getElementById("add-name");'
        'var _addFantasy=document.getElementById("add-fantasy");'
        'var _addCat=document.getElementById("add-category");'
        'var _addRegion=document.getElementById("add-region");'
        'var _addDesc=document.getElementById("add-description");'
        'var _addCmdBlock=document.getElementById("add-command-block");'
        'var _addCmdText=document.getElementById("add-command-text");'
        'var _addCopyBtn=document.getElementById("add-copy-btn");'
        'var _addGenBtn=document.getElementById("add-generate-btn");\n'

        # mouseup: set coords when Tab 1 is active
        'map.on("mouseup",function(e){'
        'if(_activeTab!=="add-point")return;'
        '_addLat.value=e.lngLat.lat.toFixed(6);'
        '_addLon.value=e.lngLat.lng.toFixed(6);'
        '_addCmdBlock.classList.add("hidden");'
        '});\n'

        'function _buildAddCmd(){'
        'var lat=_addLat.value,lon=_addLon.value;'
        'if(!lat||!lon)return null;'
        'var name=_addName.value.trim();'
        'if(!name)return null;'
        'var cat=_addCat.value;'
        'if(!cat)return null;'
        'var parts=["python utilities/map.py location"];'
        'parts.push("  --name \\""+name+"\\"");'
        'parts.push("  --lat "+lat+" --lon "+lon);'
        'parts.push("  --category "+cat);'
        'var fantasy=_addFantasy.value.trim();'
        'if(fantasy)parts.push("  --fantasy-name \\""+fantasy+"\\"");'
        'var region=_addRegion.value;'
        'if(region)parts.push("  --region "+region);'
        'var vis=document.querySelector("input[name=\'add-vis\']:checked");'
        'if(vis&&vis.value!=="public")parts.push("  --visibility "+vis.value);'
        'var desc=_addDesc.value.trim();'
        'if(desc)parts.push("  --description \\""+desc+"\\"");'
        'return parts.join(" \\\\'
        '\\n");'
        '}\n'

        '_addGenBtn.addEventListener("click",function(){'
        'var cmd=_buildAddCmd();'
        'if(!cmd){alert("Fill in: coordinates (click map), Name, and Category.");return;}'
        '_addCmdText.textContent=cmd;'
        '_addCmdBlock.classList.remove("hidden");'
        '});\n'

        '_addCopyBtn.addEventListener("click",function(){_copyText(_addCmdText.textContent,_addCopyBtn);});\n'

        # -- Tab 2: route planner --
        'var _queue=[];\n'
        'var _routeQueueList=document.getElementById("route-queue-list");'
        'var _routeRemoveBtn=document.getElementById("route-remove-btn");'
        'var _routeClearBtn=document.getElementById("route-clear-btn");'
        'var _routeGenBtn=document.getElementById("route-generate-btn");'
        'var _routeSpurCb=document.getElementById("route-spur-cb");'
        'var _routeCmdBlock=document.getElementById("route-command-block");'
        'var _routeCmdText=document.getElementById("route-command-text");'
        'var _routeCopyBtn=document.getElementById("route-copy-btn");\n'

        'function _updateQueueDisplay(){'
        'var enabled=_queue.length>0;'
        '_routeRemoveBtn.disabled=!enabled;'
        '_routeClearBtn.disabled=!enabled;'
        '_routeGenBtn.disabled=_queue.length<2;'
        '_routeCmdBlock.classList.add("hidden");'
        'if(!enabled){'
        '_routeQueueList.innerHTML=\'<li class="queue-empty">No waypoints yet.</li>\';'
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

        '_routeGenBtn.addEventListener("click",function(){'
        'if(_queue.length<2)return;'
        'var spurFlag=_routeSpurCb.checked?" --spur":"";'
        'var slugs=_queue.map(function(i){return i.slug;}).join(" ");'
        'var cmd="python utilities/map.py route "+slugs+spurFlag;'
        '_routeCmdText.textContent=cmd;'
        '_routeCmdBlock.classList.remove("hidden");'
        '});\n'

        '_routeCopyBtn.addEventListener("click",function(){_copyText(_routeCmdText.textContent,_routeCopyBtn);});\n'

        # -- Map load --
        'map.on("load",function(){\n'

        # Region overlay
        'map.addSource("regions",{type:"geojson",data:_regionGJ});\n'
        'map.addLayer({id:"regions-fill",type:"fill",minzoom:2,source:"regions",'
        'paint:{"fill-color":["coalesce",["get","fill"],"#b8892a"],'
        '"fill-opacity":["interpolate",["linear"],["zoom"],3,0.07,7,0]}});\n'
        'map.addLayer({id:"regions-line",type:"line",minzoom:2,source:"regions",'
        'paint:{"line-color":["coalesce",["get","stroke"],"#b8892a"],"line-width":2,'
        '"line-opacity":["interpolate",["linear"],["zoom"],3,0.6,7,0]}});\n'

        # Routes
        'map.addSource("routes",{type:"geojson",data:_routeGJ});\n'
        'map.addLayer({id:"routes",type:"line",minzoom:4,source:"routes",'
        'layout:{"line-cap":"butt"},'
        'paint:{"line-color":"#1a1208","line-width":3,"line-opacity":0.8,"line-dasharray":[4,4]}});\n'

        # Icons + location symbol layers
        + icons_js +
        'map.addSource("locations",{type:"geojson",data:_locGJ});\n'

        # icon_match expression
        'var _iconMatch=["case",'
        '["!=",["get","mapMarker"],null],["concat","cat-",["get","mapMarker"]],'
        '["match",["get","category"],'
        '"city","cat-city","town","cat-town","caravanserai","cat-route-node","chokepoint","cat-fortress",'
        '"mountain-pass","cat-landmark","oasis","cat-oasis","power-site","cat-sacred-site",'
        '"route-node","cat-route-node","ruins","cat-dungeon","sacred-site","cat-sacred-site",'
        '"site","cat-poi","cat-poi"]];\n'

        # Five-tier location layers (matching generate_locations_html.py tiers)
        # t: [id, cats, minzoom, fadeStart, fadeEnd, font|null, minIconSz, textSz]
        '[["locations-major",["city","landmark","fortress"],3,3.5,4,["Roboto Serif Regular","Noto Sans Bold"],0.65,15],'
        '["locations-towns",["town"],4,4.5,5,["Roboto Serif Regular","Noto Sans Regular"],0.55,13],'
        '["locations-secondary",["sacred-site","oasis","caravanserai"],5,5.5,6,["Roboto Serif Regular","Noto Sans Italic"],0.5,13],'
        '["locations-routes",["route-node","chokepoint","mountain-pass"],6,6.5,7,null,0.45,0],'
        '["locations-detail",["ruins","poi","power-site","site"],7,7.5,8,null,0.4,0]]'
        '.forEach(function(t){'
        'var id=t[0],cats=t[1],mz=t[2],fs=t[3],fe=t[4],font=t[5],minSz=t[6],tSz=t[7];'
        'var szExpr=["interpolate",["linear"],["zoom"],mz,minSz,10,minSz+0.5];'
        'var opExpr=["interpolate",["linear"],["zoom"],fs,0,fe,0.95];'
        'var catsFilter=["all",["match",["get","category"],cats,true,false],["!=",["get","mapMarker"],false]];'
        'var layout={"icon-image":_iconMatch,"icon-size":szExpr,"icon-allow-overlap":true,"icon-anchor":"center"};'
        'var paint={"icon-opacity":opExpr};'
        'if(font){'
        'layout["text-field"]=["case",["==",["get","mapLabel"],false],"",["get","label"]];'
        'layout["text-font"]=font;layout["text-size"]=tSz;'
        'layout["text-offset"]=[0,1.1];layout["text-anchor"]="top";layout["text-max-width"]=8;'
        'layout["text-allow-overlap"]=false;'
        'paint["text-color"]="#ffffff";paint["text-halo-color"]="rgba(10,8,5,0.95)";'
        'paint["text-halo-width"]=2;paint["text-opacity"]=opExpr;}'
        'map.addLayer({id:id,type:"symbol",minzoom:mz,source:"locations",'
        'filter:catsFilter,layout:layout,paint:paint});});\n'

        # Highlight source/layer for Tab 2 selected markers
        'map.addSource("highlight-source",{type:"geojson",data:{type:"FeatureCollection",features:[]}});\n'
        'map.addLayer({id:"highlight-circles",type:"circle",source:"highlight-source",'
        'paint:{"circle-radius":16,"circle-color":"rgba(0,0,0,0)",'
        '"circle-stroke-width":3,"circle-stroke-color":"#f5d060","circle-stroke-opacity":0.9}});\n'

        # Shared hover popup + click handlers across all location tiers
        'var _hoverPopup=new maplibregl.Popup({className:"ts-map-popup",offset:12,closeButton:false,closeOnClick:false});\n'
        'var _locLayerIds=["locations-major","locations-secondary","locations-routes","locations-detail"];\n'
        '_locLayerIds.forEach(function(lyr){'
        'map.on("mouseenter",lyr,function(e){'
        'map.getCanvas().style.cursor="pointer";'
        'var p=e.features[0].properties;'
        'var title=p.title||p.label||p._slug||"";'
        'var type=(p.category||"").replace(/-/g," ");'
        'var vis=p.visibility==="gm_secrets"?\'<div class="ts-popup__type" style="color:#b06040">GM only</div>\':"";\n'
        'var html=\'<div class="ts-popup">\'+'
        '\'<div class="ts-popup__title">\'+title+\'</div>\'+'
        '(type?\'<div class="ts-popup__type">\'+type+\'</div>\':"")+vis+"</div>";'
        '_hoverPopup.setLngLat(e.features[0].geometry.coordinates).setHTML(html).addTo(map);});\n'
        'map.on("mouseleave",lyr,function(){'
        'map.getCanvas().style.cursor="";_hoverPopup.remove();});\n'
        'map.on("click",lyr,function(e){'
        'var slug=e.features[0].properties._slug||e.features[0].properties.slug||"";'
        'if(!slug)return;'
        'if(_activeTab==="plan-route"){_addToQueue(slug);}'
        # Tab 1 + Tab 3: no click action on markers
        '});});\n'

        '});\n'  # end map.on('load')
    )
    # fmt: on


def _build_html(
    loc_geojson: dict,
    routes_geojson: dict,
    regions_geojson: dict,
    region_names: list,
    loc_list: list,
    route_index_html: str,
    maptiler_key: str,
) -> str:
    style_url = (
        f"https://api.maptiler.com/maps/{MAPTILER_STYLE_ID}/style.json?key={maptiler_key}"
    )
    icons_js = icon_registration_js()

    data_js = (
        f"var _locGJ = {json.dumps(loc_geojson)};\n"
        f"var _routeGJ = {json.dumps(routes_geojson)};\n"
        f"var _regionGJ = {json.dumps(regions_geojson)};\n"
        f"var _locList = {json.dumps(loc_list)};\n"
        f"var _regionList = {json.dumps(region_names)};\n"
    )

    cat_options = "\n".join(f'<option value="{c}">{c}</option>' for c in CATEGORIES)
    region_options = "\n".join(
        f'<option value="{r["slug"]}">{r["title"]}</option>' for r in region_names
    )

    panel_add = _build_panel_add_point(cat_options, region_options)
    panel_route = _build_panel_plan_route()
    app_js = _build_app_js(style_url, icons_js)

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        "<title>Map Workshop — Tarim-Shaïal</title>\n"
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/maplibre-gl@5/dist/maplibre-gl.css">\n'
        "<style>\n" + _CSS + "</style>\n"
        "</head>\n"
        "<body>\n"
        '<div id="app">\n'
        '  <div id="sidebar">\n'
        '    <div id="sidebar-header">\n'
        '      <div id="app-title">Map Workshop</div>\n'
        '      <div id="tab-bar">\n'
        '        <button class="tab-btn active" data-tab="add-point">Add Point</button>\n'
        '        <button class="tab-btn" data-tab="plan-route">Plan Route</button>\n'
        '        <button class="tab-btn" data-tab="route-index">Route Index</button>\n'
        "      </div>\n"
        "    </div>\n"
        '    <div id="panel-add-point" class="panel active">\n'
        + panel_add
        + "\n    </div>\n"
        '    <div id="panel-plan-route" class="panel">\n'
        + panel_route
        + "\n    </div>\n"
        '    <div id="panel-route-index" class="panel">\n'
        + route_index_html
        + "\n    </div>\n"
        "  </div>\n"
        '  <div id="map"></div>\n'
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
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    if not MAPTILER_KEY:
        print("ERROR: MAPTILER_KEY environment variable is not set.", file=sys.stderr)
        print("  Export it in your shell or add it to .env at vault root.", file=sys.stderr)
        return 1

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

    route_index = _build_route_index(routes_geojson)
    ri_html = _route_index_html(route_index)

    html = _build_html(
        loc_geojson=loc_geojson,
        routes_geojson=routes_geojson,
        regions_geojson=regions_geojson,
        region_names=region_names,
        loc_list=loc_list,
        route_index_html=ri_html,
        maptiler_key=MAPTILER_KEY,
    )

    OUTPUT_PATH.write_text(html, encoding="utf-8")
    print(f"\n  Written: {OUTPUT_PATH.name}")
    print(f"  Run:     open {OUTPUT_PATH.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
