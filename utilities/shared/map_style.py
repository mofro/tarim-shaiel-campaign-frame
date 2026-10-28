"""
Shared MapLibre styling for the Map Workshop, the player map and the world page.

One definition of the route and region layers, the six location tiers (with the
icon-match expression), and the hover popup (CSS + JS), so the three maps cannot
drift apart. Functions return JS / CSS fragments to splice into generated pages.

JS fragments assume a loaded `map` (maplibregl.Map). Layer fragments assume the
geojson sources "locations", "routes" and "regions" were added by the caller.

Icon mapping note: the tier icon match below reproduces what the Workshop and
player map have always drawn (capital/bridge/lake have their own icons). It is NOT
the same mapping as locations.categories.ICON_MAP, which the world page uses and
which collapses those three onto city/landmark/oasis. Unifying the two is a
visual change, so it is left as a separate decision.
"""

from __future__ import annotations

import json
import re

# ---------------------------------------------------------------------------
# Routes + regions
# ---------------------------------------------------------------------------

ROUTE_COLOR = "#b0592a"

_ROUTE_LAYOUT = {"line-cap": "butt"}
_ROUTE_PAINT = {
    "line-color": ROUTE_COLOR,
    "line-width": 3,
    "line-opacity": 0.75,
    "line-dasharray": [2.7, 2.7],
}


def _js(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


ROUTE_DIM_OPACITY = 0.28


def routes_layer_js(layer_id: str = "routes", source: str = "routes",
                    dim_hidden: bool = False) -> str:
    """JS adding the shared route line layer (dashed terracotta).

    `dim_hidden` (Workshop) fades routes the player build would drop: features
    carry `_playerVisible` (set at build time from the route_visibility rule).
    """
    paint = dict(_ROUTE_PAINT)
    if dim_hidden:
        paint["line-opacity"] = [
            "case", ["==", ["get", "_playerVisible"], True],
            _ROUTE_PAINT["line-opacity"], ROUTE_DIM_OPACITY,
        ]
    layer = {
        "id": layer_id, "type": "line", "minzoom": 4, "source": source,
        "layout": _ROUTE_LAYOUT, "paint": paint,
    }
    return f"map.addLayer({_js(layer)});\n"


# ---------------------------------------------------------------------------
# Saved journeys
# ---------------------------------------------------------------------------

JOURNEY_COLOR = "#e8a060"          # the Workshop's live travel line, kept when a journey is saved
JOURNEY_LAYER = "journeys"
JOURNEY_HIT_LAYER = "journeys-hit"
JOURNEY_DIM_OPACITY = 0.3


def journeys_layer_js(source: str = "journeys", dim_hidden: bool = False,
                      layer_id: str = JOURNEY_LAYER, hover: bool = True) -> str:
    """JS adding a solid amber line per saved journey, plus (with `hover`) a wide
    invisible layer that makes the thin line easy to hover.

    `dim_hidden` (Workshop) fades journeys the player build would drop: features
    carry `_playerVisible` (shared.journeys.annotate_player_visible). Mini-maps
    pass their own `layer_id` and `hover=False`: a plain line, no popup.
    """
    opacity: object = 0.9
    if dim_hidden:
        opacity = ["case", ["==", ["get", "_playerVisible"], True], 0.9, JOURNEY_DIM_OPACITY]
    line = {
        "id": layer_id, "type": "line", "minzoom": 3, "source": source,
        "layout": {"line-cap": "round", "line-join": "round"},
        "paint": {"line-color": JOURNEY_COLOR, "line-width": 3.5, "line-opacity": opacity},
    }
    if not hover:
        return f"map.addLayer({_js(line)});\n"
    hit = {
        "id": JOURNEY_HIT_LAYER, "type": "line", "minzoom": 3, "source": source,
        "layout": {"line-cap": "round", "line-join": "round"},
        "paint": {"line-color": "#000000", "line-width": 16, "line-opacity": 0},
    }
    return f"map.addLayer({_js(line)});\nmap.addLayer({_js(hit)});\n"


def regions_layers_js(source: str = "regions") -> str:
    """JS adding the shared region fill + outline layers (fade out by zoom 7)."""
    fill = {
        "id": "regions-fill", "type": "fill", "minzoom": 2, "source": source,
        "paint": {
            "fill-color": ["coalesce", ["get", "fill"], "#b8892a"],
            "fill-opacity": ["interpolate", ["linear"], ["zoom"], 3, 0.07, 7, 0],
        },
    }
    line = {
        "id": "regions-line", "type": "line", "minzoom": 2, "source": source,
        "paint": {
            "line-color": ["coalesce", ["get", "stroke"], "#b8892a"],
            "line-width": 2,
            "line-opacity": ["interpolate", ["linear"], ["zoom"], 3, 0.6, 7, 0],
        },
    }
    return f"map.addLayer({_js(fill)});\nmap.addLayer({_js(line)});\n"


# ---------------------------------------------------------------------------
# Basemap peak / volcano markers
# ---------------------------------------------------------------------------

# The six `icon-image: "triangle"` symbol layers of the MapTiler style
# location_components.MAPTILER_STYLE_ID (01a074c7-..., "Topo-Tarim-copy"), read
# from the style JSON on 2026-10-27. Ids contain spaces and parentheses: use them
# exactly. Only "Peak labels" is wanted, and only in the Workshop (a GM reference
# behind a checkbox); the rest are hidden on both maps, and the player map hides
# "Peak labels" too. A different style needs these ids re-checked.
BASEMAP_PEAK_LAYER = "Peak labels"
BASEMAP_HIDDEN_LAYERS = (
    "Peak labels (US)",
    "Volcano labels",
    "Volcano labels (US)",
    "Volcano labels active",
    "Volcano labels active (US)",
)
PLAYER_HIDDEN_LAYERS = BASEMAP_HIDDEN_LAYERS + (BASEMAP_PEAK_LAYER,)


def basemap_hide_js(layer_ids) -> str:
    """JS hiding basemap style layers by id once the style has loaded.

    Call it from `map.on("load")`. A missing or renamed layer is a no-op.
    """
    return (
        f"{_js(list(layer_ids))}.forEach(function(id){{"
        f'if(map.getLayer(id))map.setLayoutProperty(id,"visibility","none");}});\n'
    )


# ---------------------------------------------------------------------------
# Location tiers
# ---------------------------------------------------------------------------

_SERIF = ["Roboto Serif Regular", "Noto Sans Regular"]
_SERIF_ITALIC = ["Roboto Serif Regular", "Noto Sans Italic"]

# (layer id, categories, icon-visible zoom, label font, icon size, text size)
# Layer minzoom = zoom - 1; text fades in over [zoom - 1, zoom], icon over [zoom, zoom + 1].
LOCATION_TIERS: list[tuple[str, list[str], int, list[str], float, int]] = [
    ("locations-major",     ["city", "capital", "bridge", "landmark", "fortress"], 3, _SERIF,        0.75, 14),
    ("locations-towns",     ["town"],                                              5, _SERIF,        0.65, 12),
    ("locations-secondary", ["oasis", "lake", "caravanserai", "water-body"],       5, _SERIF_ITALIC, 0.70, 12),
    ("locations-spiritual", ["sacred-site", "power-site"],                         6, _SERIF_ITALIC, 0.70, 12),
    ("locations-routes",    ["route-node", "chokepoint", "mountain-pass"],         6, _SERIF,        0.60, 11),
    ("locations-detail",    ["ruins", "poi", "site"],                              7, _SERIF,        0.75, 10),
]

LOCATION_LAYER_IDS: list[str] = [t[0] for t in LOCATION_TIERS]

# Legacy spellings still present in data or old tooling; tolerated, not canonical.
_LEGACY_TIER_CATEGORIES = {"water-body"}

_ICON_BY_CATEGORY: list[tuple[str, str]] = [
    ("city", "cat-city"), ("capital", "cat-capital"), ("town", "cat-town"),
    ("caravanserai", "cat-route-node"), ("fortress", "cat-fortress"), ("chokepoint", "cat-fortress"),
    ("bridge", "cat-bridge"), ("landmark", "cat-landmark"), ("mountain-pass", "cat-landmark"),
    ("oasis", "cat-oasis"), ("Oasis", "cat-oasis"), ("lake", "cat-lake"), ("water-body", "cat-lake"),
    ("power-site", "cat-sacred-site"), ("route-node", "cat-route-node"), ("ruins", "cat-dungeon"),
    ("sacred-site", "cat-sacred-site"), ("site", "cat-poi"),
]
_DEFAULT_ICON = "cat-poi"


def icon_match_expr() -> list:
    """MapLibre icon-image expression: mapMarker override, else category, else cat-poi."""
    match: list = ["match", ["get", "category"]]
    for cat, icon in _ICON_BY_CATEGORY:
        match += [cat, icon]
    match.append(_DEFAULT_ICON)
    return ["case",
            ["!=", ["get", "mapMarker"], None], ["concat", "cat-", ["get", "mapMarker"]],
            match]


def tier_filter(cats: list[str]) -> list:
    """The filter a location tier starts with: its categories, and mapMarker not false."""
    return ["all", ["match", ["get", "category"], cats, True, False],
            ["!=", ["get", "mapMarker"], False]]


def location_tiers_js(source: str = "locations") -> str:
    """JS declaring `_iconMatch` and adding the six location symbol layers.

    A feature is drawn only when its category is in the tier and mapMarker is not
    false (false means 'no marker'; MapLibre forbids a zoom interpolate inside a
    case expression, so hiding by opacity is not legal -- the filter does it).
    """
    out = [f"var _iconMatch={_js(icon_match_expr())};\n"]
    for layer_id, cats, mz, font, icon_size, text_size in LOCATION_TIERS:
        layer = {
            "id": layer_id, "type": "symbol", "source": source, "minzoom": mz - 1,
            "filter": tier_filter(cats),
            "layout": {
                "icon-image": "__ICON_MATCH__", "icon-size": icon_size,
                "icon-allow-overlap": True, "icon-anchor": "center",
                "text-field": ["case", ["==", ["get", "mapLabel"], False], "", ["get", "label"]],
                "text-font": font, "text-size": text_size, "text-offset": [0, 1.1],
                "text-anchor": "top", "text-max-width": 8,
                "text-allow-overlap": False, "text-optional": True,
            },
            "paint": {
                "icon-opacity": ["interpolate", ["linear"], ["zoom"], mz, 0, mz + 1, 1],
                "text-color": "#1a1208", "text-halo-color": "#ffffff", "text-halo-width": 1.5,
                "text-opacity": ["interpolate", ["linear"], ["zoom"], mz - 1, 0, mz, 1],
            },
        }
        # Reference the shared variable rather than repeating the expression six times.
        layer_js = _js(layer).replace('"__ICON_MATCH__"', "_iconMatch")
        out.append(f"map.addLayer({layer_js});\n")
    return "".join(out)


def check_tier_coverage() -> list[str]:
    """Warnings where the tier table and locations.categories.CATEGORIES disagree."""
    from locations.categories import CATEGORIES

    in_tiers = {c for _, cats, *_ in LOCATION_TIERS for c in cats}
    warnings = [
        f"Category '{c}' is in categories.CATEGORIES but in no map tier (it will never be drawn)"
        for c in CATEGORIES if c not in in_tiers
    ]
    warnings += [
        f"Tier category '{c}' is not in categories.CATEGORIES"
        for c in sorted(in_tiers - set(CATEGORIES) - _LEGACY_TIER_CATEGORIES)
    ]
    seen: dict[str, str] = {}
    for layer_id, cats, *_ in LOCATION_TIERS:
        for c in cats:
            if c in seen:
                warnings.append(f"Category '{c}' is in two tiers: {seen[c]} and {layer_id}")
            seen[c] = layer_id
    return warnings


# ---------------------------------------------------------------------------
# Raster overlays (Topo, Satellite)
# ---------------------------------------------------------------------------

# (key, source+layer id, MapTiler tile path, default opacity). The GM owns these:
# the Workshop switches them and the devserver relays "on" and "opacity" to the
# player map (GET /api/map-overlays). Players have no control over them.
RASTER_OVERLAYS: list[tuple[str, str, str, float]] = [
    ("topo", "topo-overlay", "maps/topo-v2/{z}/{x}/{y}.png", 0.55),
    ("sat",  "sat-overlay",  "tiles/satellite-v2/{z}/{x}/{y}.jpg", 0.6),
]
OVERLAY_LAYERS: dict[str, str] = {o[0]: o[1] for o in RASTER_OVERLAYS}  # key -> layer id
OVERLAY_DEFAULT_OPACITY: dict[str, float] = {o[0]: o[3] for o in RASTER_OVERLAYS}


def raster_overlays_js(maptiler_key: str) -> str:
    """JS adding both raster overlays, hidden. Call it before any custom data
    layer so they sit beneath routes, journeys and locations."""
    out = []
    for _key, layer_id, path, opacity in RASTER_OVERLAYS:
        url = f"https://api.maptiler.com/{path}?key={maptiler_key}"
        source = {"type": "raster", "tiles": [url], "tileSize": 256, "attribution": "© MapTiler"}
        layer = {"id": layer_id, "type": "raster", "source": layer_id,
                 "layout": {"visibility": "none"}, "paint": {"raster-opacity": opacity}}
        out.append(f"map.addSource({_js(layer_id)},{_js(source)});\n")
        out.append(f"map.addLayer({_js(layer)});\n")
    return "".join(out)


# ---------------------------------------------------------------------------
# Display controls (which layers a viewer sees)
# ---------------------------------------------------------------------------

# The location-type checkboxes, in menu order: (category, label). Each category
# is one of LOCATION_TIERS' categories; the rest (ruins, site, caravanserai ...)
# have no toggle and are always drawn.
LOCATION_TYPE_TOGGLES: list[tuple[str, str]] = [
    ("city", "Cities"), ("capital", "Capitals"), ("bridge", "Bridges"),
    ("landmark", "Landmarks"), ("fortress", "Fortresses"), ("town", "Towns"),
    ("sacred-site", "Sacred Sites"), ("oasis", "Oases"), ("lake", "Lakes"),
    ("route-node", "Route Nodes"), ("poi", "POIs"),
]

# Layers each non-location toggle shows and hides.
DISPLAY_LAYER_GROUPS: dict[str, list[str]] = {
    "routes": ["routes"],
    "journeys": [JOURNEY_LAYER, JOURNEY_HIT_LAYER],
}


def tier_categories() -> dict[str, list[str]]:
    """{tier layer id: the toggle categories in that tier}."""
    toggled = {c for c, _ in LOCATION_TYPE_TOGGLES}
    return {layer_id: [c for c in cats if c in toggled]
            for layer_id, cats, *_ in LOCATION_TIERS}


def display_layer_rows_html(journeys_label: str = "Journeys") -> str:
    """Checkbox rows for the non-location display layers (routes, journeys)."""
    labels = {"routes": "Routes", "journeys": journeys_label}
    return "".join(
        f'<label class="disp-row"><input type="checkbox" class="disp-cb" '
        f'data-kind="layer" data-key="{key}" checked> {labels[key]}</label>\n'
        for key in DISPLAY_LAYER_GROUPS
    )


def display_type_grid_html() -> str:
    """The 'Locations' heading and the two-column grid of location-type checkboxes."""
    cells = "".join(
        f'<label><input type="checkbox" class="disp-cb" data-kind="type" '
        f'data-key="{cat}" checked> {label}</label>\n'
        for cat, label in LOCATION_TYPE_TOGGLES
    )
    return f'<div class="it-heading">Locations</div>\n<div class="it-grid">\n{cells}</div>\n'


def display_controls_css(touch: bool = False) -> str:
    """CSS for the location grid. `touch` gives every row a 44px tap target."""
    css = """\
.it-heading { font-size:10px; text-transform:uppercase; letter-spacing:0.07em; color:#8a7a5a; margin-bottom:3px; }
.it-grid { display:grid; grid-template-columns:1fr 1fr; gap:2px 10px; }
.it-grid label { display:flex; align-items:center; gap:5px; cursor:pointer; color:#c8b890;
  font-size:10px; text-transform:none; letter-spacing:0; white-space:nowrap; margin-top:0; }
.it-grid input[type=checkbox] { accent-color:#b8922c; cursor:pointer; }
"""
    if touch:
        css += """\
.disp-layers { display:grid; grid-template-columns:1fr 1fr; gap:0 10px; }
.it-grid { gap:0 10px; }
.disp-row, .it-grid label { box-sizing:border-box; min-height:44px; padding:0; touch-action:manipulation; }
.disp-row { display:flex; align-items:center; gap:8px; cursor:pointer; color:#e8dcc4; font-size:14px; }
.it-grid label { gap:8px; font-size:13px; line-height:1.15; color:#e8dcc4; white-space:normal; }
.it-grid label:last-child:nth-child(odd) { grid-column:1 / -1; }
.disp-row input[type=checkbox], .it-grid input[type=checkbox] { width:22px; height:22px; flex:none;
  accent-color:#b8922c; cursor:pointer; }
.it-heading { font-size:11px; margin:0 0 2px; }
.disp-layers + .it-heading { margin-top:6px; }
"""
    return css


def display_controls_js(storage: str, key: str, layers: dict | None = None) -> str:
    """JS owning the type / routes / journeys toggles.

    Defines `_tierCats`, `_dispState` and `_dispLoad` / `_dispSave` / `_dispApply` /
    `_dispWire`. `storage` ("localStorage" or "sessionStorage") holds one JSON blob
    under `key`; every access sits in try/catch so a blocked store changes nothing
    but persistence.

    `_dispApply` is the only place that sets filters on the tier layers, routes
    and journeys. Whatever else must narrow one of them (the Workshop's player
    preview, the journey being edited) defines `_dispExtra(layerId)` returning an
    array of filter conditions (or null) and calls `_dispApply()`; a second
    `setFilter` on those layers would overwrite this one.

    Only categories whose checkbox is off are excluded: the categories with no
    toggle always show, on both maps.
    """
    groups = layers if layers is not None else DISPLAY_LAYER_GROUPS
    base = {lid: tier_filter(cats) for lid, cats, *_ in LOCATION_TIERS}
    types = {c: True for c, _ in LOCATION_TYPE_TOGGLES}
    return f"""\
var _tierCats={_js(tier_categories())};
var _tierBase={_js(base)};
var _dispLayers={_js(groups)};
var _dispState={{types:{_js(types)},layers:{_js({k: True for k in groups})}}};
var _DISP_KEY={_js(key)};
function _dispLoad(){{
  try{{
    var raw={storage}.getItem(_DISP_KEY);if(!raw)return;
    var v=JSON.parse(raw);if(!v||typeof v!=="object")return;
    ["types","layers"].forEach(function(g){{
      var from=v[g];if(!from||typeof from!=="object")return;
      Object.keys(_dispState[g]).forEach(function(k){{
        if(typeof from[k]==="boolean")_dispState[g][k]=from[k];}});}});
  }}catch(_e){{}}
}}
function _dispSave(){{
  try{{{storage}.setItem(_DISP_KEY,JSON.stringify(_dispState));}}catch(_e){{}}
}}
function _dispFilter(lyr,base){{
  var c=base?[base]:[];
  var x=typeof _dispExtra==="function"?_dispExtra(lyr):null;
  if(x)c=c.concat(x);
  return c.length===0?null:(c.length===1?c[0]:["all"].concat(c));
}}
function _dispApply(){{
  if(typeof map==="undefined"||!map)return;
  Object.keys(_tierCats).forEach(function(lyr){{
    if(!map.getLayer(lyr))return;
    var off=_tierCats[lyr].filter(function(c){{return !_dispState.types[c];}});
    var conds=[_tierBase[lyr]];
    if(off.length)conds.push(["!",["match",["get","category"],off,true,false]]);
    var x=typeof _dispExtra==="function"?_dispExtra(lyr):null;
    if(x)conds=conds.concat(x);
    map.setFilter(lyr,conds.length===1?conds[0]:["all"].concat(conds));
  }});
  Object.keys(_dispLayers).forEach(function(k){{
    _dispLayers[k].forEach(function(lyr){{
      if(!map.getLayer(lyr))return;
      map.setLayoutProperty(lyr,"visibility",_dispState.layers[k]?"visible":"none");
      map.setFilter(lyr,_dispFilter(lyr,null));
    }});
  }});
}}
function _dispWire(){{
  document.querySelectorAll(".disp-cb").forEach(function(cb){{
    var group=cb.dataset.kind==="type"?_dispState.types:_dispState.layers,k=cb.dataset.key;
    if(k in group)cb.checked=group[k];
    cb.addEventListener("change",function(){{group[k]=cb.checked;_dispSave();_dispApply();}});
  }});
}}
_dispLoad();
_dispWire();
"""


# ---------------------------------------------------------------------------
# Hover popup
# ---------------------------------------------------------------------------

POPUP_DESC_MAX = 200

_PLACEHOLDER_RE = re.compile(r"^\s*placeholder\b", re.I)
_GM_INLINE_RE = re.compile(r"\{gm:[^}]*\}", re.I)
_WIKILINK_RE = re.compile(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]")
# Descriptions written as session notes ("Session 0 Seeker awakening collapse site")
# are GM/campaign bookkeeping, not map blurbs. Fail closed for players.
_CAMPAIGN_META_RE = re.compile(r"\bsession\s*\d+|\bawakening\b", re.I)


def popup_description(raw, player_safe: bool = False) -> str:
    """Short popup blurb from a location's `description`; '' means show none.

    Drops the 'PLACEHOLDER ...' text that add_location.py seeds, strips inline GM
    redactions and wikilink syntax, collapses whitespace, and truncates to
    POPUP_DESC_MAX at a word boundary. With player_safe, also drops descriptions
    that read as campaign/session notes.
    """
    if not raw:
        return ""
    text = _GM_INLINE_RE.sub("", str(raw))
    text = _WIKILINK_RE.sub(r"\1", text)
    text = " ".join(text.split())
    if not text or _PLACEHOLDER_RE.match(text):
        return ""
    if player_safe and _CAMPAIGN_META_RE.search(text):
        return ""
    if len(text) > POPUP_DESC_MAX:
        text = text[: POPUP_DESC_MAX - 1].rsplit(" ", 1)[0].rstrip(" ,;:—-.") + "…"
    return text


def popup_css() -> str:
    return """\
.ts-popup { font-family: Georgia, serif; max-width: 260px; }
.ts-popup__title { font-size: 13px; font-weight: bold; color: #1a1208; }
.ts-popup__type { font-size: 11px; color: #6a5a3a; margin-top: 2px; }
.ts-popup__desc { font-size: 12px; color: #3a2e1a; margin-top: 4px; line-height: 1.35; }
.ts-popup__gm { font-size: 11px; color: #b06040; margin-top: 2px; }
.ts-popup__leg { font-size: 12px; color: #3a2e1a; margin-top: 3px; line-height: 1.3; }
.ts-map-popup .maplibregl-popup-content { background: #f5f0e8; padding: 8px 12px;
  border-radius: 3px; box-shadow: 0 2px 8px rgba(0,0,0,0.4); }
"""


def hover_popup_js(gm_badge: bool = False, tap_to_open: bool = False) -> str:
    """JS adding a hover popup (title, type, description) to every location tier.

    Defines `_hoverPopup`, `_locLayerIds` and `_escHtml`. gm_badge adds a 'GM only'
    line for gm_secrets features; leave it False on any player-facing page so the
    string never ships there. tap_to_open also opens the popup on click/tap (touch
    screens do not reliably fire mouseenter) and closes it on a tap elsewhere.
    """
    badge = (
        """if(p.visibility==="gm_secrets")h+='<div class="ts-popup__gm">GM only</div>';"""
        if gm_badge else ""
    )
    tap = (
        """
map.on("click",function(e){
  var hit=map.queryRenderedFeatures(e.point,{layers:_locLayerIds});
  if(!hit.length){_hoverPopup.remove();return;}
  _showLocPopup(hit[0]);
});""" if tap_to_open else ""
    )
    return f"""\
var _hoverPopup=new maplibregl.Popup({{className:"ts-map-popup",offset:12,closeButton:false,closeOnClick:false,maxWidth:"280px"}});
var _locLayerIds={_js(LOCATION_LAYER_IDS)};
function _escHtml(s){{return String(s==null?"":s).replace(/[&<>"']/g,function(c){{
  return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c];}});}}
function _locPopupHtml(p){{
  var h='<div class="ts-popup"><div class="ts-popup__title">'+_escHtml(p.title||p.label||p._slug)+'</div>';
  var type=(p.category||"").replace(/-/g," ");
  if(type)h+='<div class="ts-popup__type">'+_escHtml(type)+'</div>';
  if(p.popupDesc)h+='<div class="ts-popup__desc">'+_escHtml(p.popupDesc)+'</div>';
  {badge}
  return h+'</div>';
}}
function _showLocPopup(f){{
  _hoverPopup.setLngLat(f.geometry.coordinates).setHTML(_locPopupHtml(f.properties)).addTo(map);
}}
_locLayerIds.forEach(function(lyr){{
  map.on("mouseenter",lyr,function(e){{map.getCanvas().style.cursor="pointer";_showLocPopup(e.features[0]);}});
  map.on("mouseleave",lyr,function(){{map.getCanvas().style.cursor="";_hoverPopup.remove();}});
}});{tap}
"""


def journey_hover_js(info_var: str = "_jrnInfo", tap_to_open: bool = False) -> str:
    """JS adding a hover popup to the journey layer: name, one row per leg, total.

    `info_var` names a page global holding {journey id: shared.journeys.popup_info}.
    It is read when the popup opens, so a page may reassign it after a save.
    Self-contained (its own popup and escaper) so it works on pages that define
    different location popups. A location marker under the pointer wins, so the
    two popups never stack. tap_to_open also opens on tap and closes on a tap
    elsewhere (touch screens do not fire mouseenter).
    """
    tap = (
        f"""
map.on("click",function(e){{
  var hit=map.queryRenderedFeatures(e.point,{{layers:["{JOURNEY_HIT_LAYER}"]}});
  if(!hit.length){{_jrnPopup.remove();return;}}
  _jrnShow({{features:hit,point:e.point,lngLat:e.lngLat}});
}});""" if tap_to_open else ""
    )
    return f"""\
var _jrnPopup=new maplibregl.Popup({{className:"ts-map-popup",offset:8,closeButton:false,closeOnClick:false,maxWidth:"340px"}});
function _jrnEsc(s){{return String(s==null?"":s).replace(/[&<>"']/g,function(c){{
  return {{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}}[c];}});}}
function _jrnPopupHtml(id){{
  var i={info_var}[id];if(!i)return "";
  var h='<div class="ts-popup"><div class="ts-popup__title">'+_jrnEsc(i.name)+'</div>';
  (i.legs||[]).forEach(function(l){{
    h+='<div class="ts-popup__leg">'+_jrnEsc(l.from)+' &rarr; '+_jrnEsc(l.to)+' &middot; '+_jrnEsc(l.how)+' &middot; '+_jrnEsc(l.km)+' &middot; '+_jrnEsc(l.time)+'</div>';
  }});
  return h+'<div class="ts-popup__type">'+_jrnEsc(i.total)+'</div></div>';
}}
function _jrnOverLocation(pt){{
  var ids=map.getStyle().layers.filter(function(l){{return /^(gm-)?locations-/.test(l.id);}}).map(function(l){{return l.id;}});
  return ids.length>0&&map.queryRenderedFeatures(pt,{{layers:ids}}).length>0;
}}
function _jrnShow(e){{
  var f=e.features&&e.features[0];if(!f)return;
  if(_jrnOverLocation(e.point)){{_jrnPopup.remove();return;}}
  var h=_jrnPopupHtml(f.properties.id);if(!h)return;
  _jrnPopup.setLngLat(e.lngLat).setHTML(h).addTo(map);
}}
map.on("mouseenter","{JOURNEY_HIT_LAYER}",function(e){{map.getCanvas().style.cursor="pointer";_jrnShow(e);}});
map.on("mouseleave","{JOURNEY_HIT_LAYER}",function(){{map.getCanvas().style.cursor="";_jrnPopup.remove();}});{tap}
"""
