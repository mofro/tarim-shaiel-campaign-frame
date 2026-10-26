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
            "filter": ["all", ["match", ["get", "category"], cats, True, False],
                       ["!=", ["get", "mapMarker"], False]],
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
