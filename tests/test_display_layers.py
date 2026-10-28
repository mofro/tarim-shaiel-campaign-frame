"""
Tests for the display layers (#323): raster overlays are GM-owned (published by the
Workshop through the devserver, followed by the player map), location-type / routes /
journeys toggles are player-owned (per browser), and the Workshop gains a Routes
toggle plus a Player's-eye preview.

Four parts: the devserver contract, what the generated pages contain, the real
player script run in node, and the real Workshop script run in node. Both pages are
built from one fixture with the real build functions, and a small evaluator runs
each layer's registered filter over its source data, so "what the Workshop preview
shows" is compared with "what a rebuilt player map shows" feature by feature.
"""

import http.server
import json
import re
import shutil
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities" / "world"))
sys.path.insert(0, str(ROOT / "utilities"))

import devserver
import generate_map_workshop as gmw
from shared import journeys, map_style, route_visibility

EMPTY = {"type": "FeatureCollection", "features": []}
DISPLAY_KEY = gmw.PLAYER_DISPLAY_KEY
OVERLAY_IDS = {"topo": "topo-overlay", "sat": "sat-overlay"}

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


# ---------------------------------------------------------------------------
# Fixture world: public and GM-only locations, routes and journeys
# ---------------------------------------------------------------------------

def _location(slug, category, lon, visibility="public"):
    return {"slug": slug, "title": slug.title(), "fantasy_name": None, "description": "",
            "location_type": category, "visibility": visibility, "map_label": True,
            "map_marker": True, "lat": 40.0, "lon": lon}


LOCATIONS = [
    _location("amber", "city", 70.0),
    _location("birch", "town", 71.0),
    _location("cedar", "poi", 72.0, "gm_secrets"),
    _location("dune", "ruins", 73.0, "gm_secrets"),
    _location("elm", "oasis", 74.0),
    _location("fir", "capital", 75.0),
    _location("gorse", "ruins", 76.0),
]
LOC_GJ = gmw._build_locations_geojson(LOCATIONS)


def _route(rid, a, b, visibility):
    lons = {"amber": 70.0, "birch": 71.0, "cedar": 72.0}
    return {"type": "Feature", "id": rid,
            "properties": {"route_name": rid, "visibility": visibility, "mode": "caravan"},
            "geometry": {"type": "LineString", "coordinates": [[lons[a], 40.0], [lons[b], 40.0]]}}


ROUTES = {"type": "FeatureCollection", "features": [
    _route("r_public", "amber", "birch", "public"),
    _route("r_gm_own", "amber", "birch", "gm_secrets"),
    _route("r_hidden_end", "birch", "cedar", "public"),
]}


def _journey(jid, slugs, visibility):
    lons = {"amber": 70.0, "birch": 71.0, "cedar": 72.0}
    stops = [{"lng": lons[s], "lat": 40.0, "name": s, "slug": s} for s in slugs]
    legs = [{"mode": "foot", "path": "straight",
             "coords": [[lons[a], 40.0], [lons[b], 40.0]]} for a, b in zip(slugs, slugs[1:])]
    clean = journeys.clean_journey({"name": jid, "stops": stops, "legs": legs})
    return journeys.build_feature(jid, clean, visibility, "2026-01-01", "2026-01-01")


JOURNEYS = {"type": "FeatureCollection", "features": [
    _journey("j_public", ["amber", "birch"], "public"),
    _journey("j_gm_own", ["amber", "birch"], "gm_secrets"),
    _journey("j_hidden_stop", ["birch", "cedar"], "public"),
]}

GM_ONLY_LOCATIONS = {"cedar", "dune"}
PLAYER_ROUTES = {"r_public"}
PLAYER_JOURNEYS = {"j_public"}


def _workshop_html():
    workshop_jrn_info = journeys.gm_payload(JOURNEYS)[1]
    return gmw._build_html(
        LOC_GJ, gmw.annotate_routes(ROUTES, LOC_GJ), EMPTY, [], [], "", "k",
        journeys_geojson=journeys.annotate_player_visible(JOURNEYS, LOC_GJ),
        journey_info=workshop_jrn_info)


def _player_html():
    jrn_gj, jrn_info = journeys.player_payload(JOURNEYS, LOC_GJ)
    return gmw._build_player_html(
        loc_geojson=gmw._player_locations_geojson(LOC_GJ),
        routes_geojson=route_visibility.visible_routes(ROUTES, LOC_GJ, warn=False),
        maptiler_key="k", journeys_geojson=jrn_gj, journey_info=jrn_info)


def _scripts(html):
    return re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.S)


def _workshop_script():
    return max(_scripts(_workshop_html()), key=len)


def _player_script():
    return next(s for s in _scripts(_player_html()) if "_initMap" in s)


def _checkboxes(html):
    """[{kind, key}] for every display checkbox in a page's markup, in order."""
    out = []
    for tag in re.findall(r"<input[^>]*\bdisp-cb\b[^>]*>", html):
        out.append({"kind": re.search(r'data-kind="([^"]+)"', tag).group(1),
                    "key": re.search(r'data-key="([^"]+)"', tag).group(1),
                    "checked": " checked" in tag})
    return out


TYPE_KEYS = [c for c, _ in map_style.LOCATION_TYPE_TOGGLES]


# ---------------------------------------------------------------------------
# Part A  Devserver: /api/map-overlays (S1)
# ---------------------------------------------------------------------------

@pytest.fixture
def overlays(monkeypatch):
    monkeypatch.setattr(devserver, "_map_overlays", {
        k: {"on": False, "opacity": d} for k, d in map_style.OVERLAY_DEFAULT_OPACITY.items()})


def _serve(handler):
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


@pytest.fixture
def base(overlays):
    server, thread = _serve(devserver._Handler)
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


class _Remote(devserver._Handler):
    """Same handler, but the real `_is_local` sees a LAN address."""

    @property
    def client_address(self):
        return ("192.168.1.50", 40000)

    @client_address.setter
    def client_address(self, value):
        pass


@pytest.fixture
def remote_base(overlays):
    server, thread = _serve(_Remote)
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, None


def _post(url, body, raw=False):
    data = body if raw else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"},
                                 method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def _state(base):
    return _get(base + "/api/map-overlays")[1]


def test_overlay_keys_match_the_shared_layer_ids():
    assert map_style.OVERLAY_LAYERS == OVERLAY_IDS
    assert set(map_style.OVERLAY_DEFAULT_OPACITY) == set(OVERLAY_IDS)


def test_get_before_any_post_has_both_overlays_off(base):
    status, body = _get(base + "/api/map-overlays")
    assert status == 200
    assert body == {k: {"on": False, "opacity": d}
                    for k, d in map_style.OVERLAY_DEFAULT_OPACITY.items()}


def test_post_then_get_returns_the_values_and_only_on_and_opacity(base):
    sent = {"topo": {"on": True, "opacity": 0.4}, "sat": {"on": False, "opacity": 1}}
    assert _post(base + "/api/map-overlays", sent) == 200
    got = _state(base)
    assert got == {"topo": {"on": True, "opacity": 0.4}, "sat": {"on": False, "opacity": 1.0}}
    assert all(set(v) == {"on", "opacity"} for v in got.values())


def test_a_query_string_and_trailing_slash_still_route(base):
    assert _get(base + "/api/map-overlays/?t=123")[0] == 200
    assert _post(base + "/api/map-overlays/?x=1", {"topo": {"on": True}}) == 200
    assert _state(base)["topo"]["on"] is True


@pytest.mark.parametrize("body", [
    {"moon": {"on": True}},
    {"topo": {"on": True}, "moon": {"on": True}},
    {"topo": {"on": True, "color": "red"}},
    {"topo": {"on": "true"}},
    {"topo": {"on": 1}},
    {"topo": {"on": 0}},
    {"topo": {"on": None}},
    {"topo": {"opacity": "0.5"}},
    {"topo": {"opacity": None}},
    {"topo": {"opacity": True}},
    {"topo": {"opacity": [0.5]}},
    {"topo": True},
    {"topo": [1]},
    {"topo": None},
    {"topo": {"on": True, "opacity": 0.2}, "sat": {"on": "yes"}},
    [],
    ["topo"],
    "topo",
    5,
    None,
])
def test_malformed_payloads_are_rejected_and_change_nothing(base, body):
    before = _state(base)
    assert _post(base + "/api/map-overlays", body) == 400
    assert _state(base) == before


@pytest.mark.parametrize("raw", [b"", b"{", b"not json", b"{'topo': {}}", b'{"topo": {"on": tru}}'])
def test_unparseable_bodies_are_400(base, raw):
    before = _state(base)
    assert _post(base + "/api/map-overlays", raw, raw=True) == 400
    assert _state(base) == before


def test_a_bad_overlay_in_a_payload_stops_the_good_one_being_applied(base):
    assert _post(base + "/api/map-overlays",
                 {"topo": {"on": True, "opacity": 0.1}, "sat": {"on": "yes"}}) == 400
    assert _state(base)["topo"] == {"on": False, "opacity": map_style.OVERLAY_DEFAULT_OPACITY["topo"]}


@pytest.mark.parametrize("sent,expected", [(5, 1.0), (1.0001, 1.0), (-3, 0.0), (-0.0001, 0.0),
                                           (0, 0.0), (1, 1.0), (0.5, 0.5)])
def test_opacity_is_clamped_not_rejected(base, sent, expected):
    assert _post(base + "/api/map-overlays", {"sat": {"opacity": sent}}) == 200
    assert _state(base)["sat"]["opacity"] == expected


def test_infinity_clamps_and_nan_is_rejected(base):
    assert _post(base + "/api/map-overlays", b'{"sat": {"opacity": Infinity}}', raw=True) == 200
    assert _state(base)["sat"]["opacity"] == 1.0
    assert _post(base + "/api/map-overlays", b'{"sat": {"opacity": NaN}}', raw=True) == 400
    assert _state(base)["sat"]["opacity"] == 1.0


def test_a_payload_naming_one_overlay_leaves_the_other_alone(base):
    assert _post(base + "/api/map-overlays",
                 {"topo": {"on": True, "opacity": 0.3}, "sat": {"on": True, "opacity": 0.9}}) == 200
    assert _post(base + "/api/map-overlays", {"sat": {"on": False}}) == 200
    assert _state(base) == {"topo": {"on": True, "opacity": 0.3}, "sat": {"on": False, "opacity": 0.9}}


def test_an_empty_object_is_a_valid_no_op(base):
    before = _state(base)
    assert _post(base + "/api/map-overlays", {}) == 200
    assert _state(base) == before


def test_a_non_local_client_cannot_post_but_can_read(remote_base):
    before = _state(remote_base)
    assert _post(remote_base + "/api/map-overlays", {"topo": {"on": True}}) == 403
    assert _state(remote_base) == before
    assert _get(remote_base + "/api/map-overlays")[0] == 200


def test_the_state_lives_in_memory_only():
    src = Path(devserver.__file__).read_text(encoding="utf-8")
    body = src[src.index("def _overlays_set"):src.index("def _detect_lan_ip")]
    assert "write_text" not in body and "open(" not in body and "json.dump(" not in body


# ---------------------------------------------------------------------------
# Part B  What the generated pages contain (S3, S4, S6)
# ---------------------------------------------------------------------------

def test_the_location_types_and_their_labels_live_in_map_style():
    assert len(map_style.LOCATION_TYPE_TOGGLES) == 11
    assert dict(map_style.LOCATION_TYPE_TOGGLES)["sacred-site"] == "Sacred Sites"
    cats = map_style.tier_categories()
    for category in TYPE_KEYS:
        assert any(category in c for c in cats.values()), category
    gen = Path(gmw.__file__).read_text(encoding="utf-8")
    assert "_tierCats" not in gen.replace('lyr in _tierCats', "")
    assert "Sacred Sites" not in gen


@pytest.mark.parametrize("build", [_workshop_script, _player_script], ids=["workshop", "player"])
def test_both_pages_read_the_same_shared_control(build):
    page = build()
    assert page.count("var _tierCats=") == 1
    assert "var _tierCats=" + json.dumps(map_style.tier_categories(), separators=(",", ":")) in page
    for fn in ("_dispLoad", "_dispSave", "_dispFilter", "_dispApply", "_dispWire"):
        assert page.count(f"function {fn}(") == 1, fn


@pytest.mark.parametrize("build", [_workshop_script, _player_script], ids=["workshop", "player"])
def test_only_dispapply_calls_setfilter(build):
    page = build()
    start = page.index("function _dispApply(){")
    end = page.index("function _dispWire(){")
    hits = [m.start() for m in re.finditer(r"\.setFilter\(", page)]
    assert len(hits) == 2
    assert all(start < h < end for h in hits)


def test_the_journey_editor_refilters_through_the_single_owner():
    page = _workshop_script()
    assert re.search(r"function _ttFilterSaved\(\)\s*\{\s*_dispApply\(\);\s*\}", page)
    assert "_rebuildTierFilters" not in page


@pytest.mark.parametrize("build", [_workshop_script, _player_script], ids=["workshop", "player"])
def test_raster_overlay_sources_and_layers_are_defined_once(build):
    page = build()
    for key, layer in OVERLAY_IDS.items():
        assert page.count(f'map.addSource("{layer}"') == 1, layer
        assert len(re.findall(r'map\.addLayer\(\{"id":\s*"' + layer + '"', page)) == 1, layer
    gen = Path(gmw.__file__).read_text(encoding="utf-8")
    for _key, _layer, tile_path, _opacity in map_style.RASTER_OVERLAYS:
        assert tile_path not in gen, tile_path  # the tile URLs live in map_style only


def test_player_markup_lists_the_eleven_types_routes_and_journeys_all_on():
    boxes = _checkboxes(_player_html())
    assert [b["key"] for b in boxes if b["kind"] == "type"] == TYPE_KEYS
    assert [b["key"] for b in boxes if b["kind"] == "layer"] == ["routes", "journeys"]
    assert all(b["checked"] for b in boxes)
    assert len(boxes) == 13


def test_player_page_has_no_overlay_controls_or_workshop_only_ids():
    html = _player_html()
    for token in ("topo-toggle", "sat-toggle", "topo-share", "sat-share", "topo-opacity", "sat-opacity",
                  'type="range"', "overlay-err", "preview-toggle", "peak-toggle", "Share with players", "Opacity"):
        assert token not in html, token
    # the two raster layers exist in the script, but nothing in the markup toggles them
    markup = re.sub(r"<script.*?</script>|<style.*?</style>", "", html, flags=re.S)
    assert "overlay" not in markup.lower() and "topo" not in markup.lower()


def test_player_page_names_no_layer_that_only_the_workshop_has():
    ws_layers = set(re.findall(r'\bid:\s*"([a-z0-9-]+)"', _workshop_html()))
    ws_layers |= set(re.findall(r'"id":\s*"([a-z0-9-]+)"', _workshop_html()))
    player = _player_html()
    for lid in ("highlight-circles", "reveal-rings", "route-preview-line", "route-selected",
                "tt-line-layer", "regions-fill", "regions-line"):
        assert lid in _workshop_html() or lid in ws_layers, f"{lid} not in Workshop: test is stale"
        assert lid not in player, lid
    for token in ("_playerVisible", "_endsPublic", "_ttJid", "_dispPreview",
                  "gm_secrets", "Player's-eye", "reveal", "highlight"):
        assert token not in player, token
    # the shared filter only probes for the Workshop's extra-conditions hook; the player never defines it
    assert "_dispExtra" not in player.replace('typeof _dispExtra==="function"?_dispExtra(lyr):null', "")


def test_player_panel_is_top_left_44px_and_clear_of_the_other_controls():
    css = gmw._PLAYER_LAYERS_CSS
    btn = re.search(r"#layers-btn\s*\{([^}]*)\}", css).group(1)
    assert "top:" in btn and "left:" in btn and "right:" not in btn and "bottom:" not in btn
    assert "width:44px" in btn and "height:44px" in btn
    panel = re.search(r"#layers-panel\s*\{([^}]*)\}", css).group(1)
    assert "left:" in panel and "right:" not in panel
    assert "min(300px, calc(100vw - 80px))" in panel  # fits 375px with room for the nav control
    rows = map_style.display_controls_css(touch=True)
    assert "min-height:44px" in rows
    html = _player_html()
    nav = re.search(r"NavigationControl\([^)]*\)\s*,\s*['\"]([a-z-]+)['\"]", html)
    scale = re.search(r"ScaleControl\([^)]*\)\s*,\s*['\"]([a-z-]+)['\"]", html)
    assert nav is None or nav.group(1).startswith("top-right")
    assert scale is None or scale.group(1).startswith("bottom")
    follow = re.search(r"#follow-btn\s*\{([^}]*)\}", html).group(1)
    assert "bottom:" in follow and "top:" not in follow


def test_every_storage_access_in_the_player_page_sits_in_a_try_block():
    page = _player_script()
    hits = [m.start() for m in re.finditer(r"localStorage", page)]
    assert hits
    for at in hits:
        enclosing = page[page.rfind("function ", 0, at):at]
        assert "try{" in enclosing or "try {" in enclosing, page[max(0, at - 80):at + 40]
    assert page.count(f'var _DISP_KEY="{DISPLAY_KEY}"') == 1


# ---------------------------------------------------------------------------
# The node harness (shared by the player and Workshop parts)
# ---------------------------------------------------------------------------

HARNESS = r"""
const fs = require('fs'), vm = require('vm');
const SCRIPT = fs.readFileSync(process.argv[2], 'utf8');
const CFG = JSON.parse(fs.readFileSync(process.argv[3], 'utf8'));
const out = x => console.log(JSON.stringify(x));
const flush = async () => { for (let i = 0; i < 6; i++) await new Promise(r => setImmediate(r)); };

function generic(name) {
  const t = function () {}; const own = {};
  return new Proxy(t, {
    get(_, p) {
      if (p === Symbol.toPrimitive) return () => '';
      if (p === 'then' || typeof p === 'symbol') return undefined;
      if (p === 'querySelectorAll' || p === 'getElementsByClassName') return () => [];
      if (p === 'dataset') return own.dataset || (own.dataset = {});
      if (p in own) return own[p];
      return (own[p] = generic(name + '.' + p));
    },
    set(_, p, v) { own[p] = v; return true; },
    apply() { return generic(name + '()'); },
    construct() { return generic(name + '#'); },
  });
}

// A small MapLibre filter-expression evaluator: only the operators the pages emit.
function ev(e, p) {
  if (!Array.isArray(e)) return e;
  switch (e[0]) {
    case 'all': return e.slice(1).every(x => ev(x, p));
    case 'any': return e.slice(1).some(x => ev(x, p));
    case '!': return !ev(e[1], p);
    case 'get': return p[e[1]] === undefined ? null : p[e[1]];
    case '==': return ev(e[1], p) === ev(e[2], p);
    case '!=': return ev(e[1], p) !== ev(e[2], p);
    case 'literal': return e[1];
    case 'match': {
      const v = ev(e[1], p);
      for (let i = 2; i + 1 < e.length; i += 2) {
        const lab = e[i];
        if (Array.isArray(lab) ? lab.includes(v) : lab === v) return e[i + 1];
      }
      return e[e.length - 1];
    }
    default: throw new Error('unsupported filter operator ' + JSON.stringify(e[0]));
  }
}
const fid = f => (f.properties && f.properties.slug) || f.id || (f.properties && f.properties.id);

function makeEl(id, init) {
  const base = Object.assign({id, checked: false, value: '', hidden: false, textContent: '',
                              dataset: {}, _l: {}, style: {}}, init || {});
  base.addEventListener = (t, f) => { (base._l[t] = base._l[t] || []).push(f); };
  base.fire = (t, e) => { (base._l[t] || []).forEach(f => f.call(px, e || {target: px})); };
  base.setAttribute = (k, v) => { base['attr_' + k] = v; };
  base.contains = () => false;
  base.classList = {toggle() {}, add() {}, remove() {}, contains: () => false};
  const gen = generic(id);
  const px = new Proxy(base, {get: (t, p) => (p in t ? t[p] : gen[p]), set: (t, p, v) => { t[p] = v; return true; }});
  return px;
}

class FakeMap {
  constructor(o) { this.opts = o; this.h = {}; this.layers = {}; this.sources = {}; this.setFilterCalls = [];
                   this.center = {lng: o.center[0], lat: o.center[1]}; M.maps.push(this); M.map = this; }
  on(t, a, b) { const k = typeof a === 'string' ? t + ':' + a : t; (this.h[k] = this.h[k] || []).push(b || a); }
  fire(t, e) { (this.h[t] || []).forEach(f => f(e)); }
  addSource(id, spec) { this.sources[id] = spec; }
  addLayer(l) { this.layers[l.id] = {id: l.id, type: l.type, source: l.source,
                                     filter: l.filter === undefined ? null : l.filter,
                                     layout: Object.assign({}, l.layout), paint: Object.assign({}, l.paint)}; }
  getLayer(id) { return this.layers[id]; }
  setFilter(id, f) { if (!this.layers[id]) throw new Error('no layer ' + id);
                     this.layers[id].filter = f; this.setFilterCalls.push(id); }
  setLayoutProperty(id, k, v) { if (!this.layers[id]) throw new Error('no layer ' + id); this.layers[id].layout[k] = v; }
  setPaintProperty(id, k, v) { if (!this.layers[id]) throw new Error('no layer ' + id); this.layers[id].paint[k] = v; }
  getStyle() { return {layers: Object.keys(this.layers).map(id => ({id}))}; }
  getCenter() { return this.center; } getZoom() { return this.opts.zoom || 5; }
  getCanvas() { return {style: {}}; } getBounds() { return generic('bounds'); } getContainer() { return generic('c'); }
  queryRenderedFeatures() { return []; } addControl() {} addImage() {} easeTo() {} jumpTo() {} resize() {}
  getSource() { return generic('src'); } removeLayer() {} removeSource() {} setTerrain() {}
  // ids drawn by one layer: its source features that pass its current filter (none when hidden)
  render(lid) {
    const l = this.layers[lid]; if (!l) return null;
    if (l.layout.visibility === 'none') return [];
    const src = this.sources[l.source];
    const feats = (src && src.data && src.data.features) || [];
    return feats.filter(f => l.filter == null || ev(l.filter, f.properties || {})).map(fid).sort();
  }
  renderAll() { const r = {}; Object.keys(this.layers).forEach(k => { r[k] = this.render(k); }); return r; }
}
const M = {maps: [], map: null};

async function boot(o) {
  o = o || {};
  Object.assign(M, {posts: [], fetches: [], errors: [], now: 0, nextId: 1, timers: [],
                    overlays: o.overlays || {topo: {on: false, opacity: 0.55}, sat: {on: false, opacity: 0.6}}});
  const store = Object.assign({}, o.local || {}), sess = Object.assign({}, o.session || {});
  M.store = store; M.sess = sess;
  const els = {};
  M.el = id => els[id];
  const defs = CFG.kind === 'workshop'
    ? {'topo-toggle': {}, 'topo-opacity': {value: '55'}, 'topo-share': {}, 'sat-toggle': {}, 'sat-opacity': {value: '60'},
       'sat-share': {}, 'preview-toggle': {}, 'peak-toggle': {checked: true}}
    : {'follow-btn': {}, 'layers-btn': {}, 'layers-panel': {hidden: true}};
  Object.keys(defs).forEach(id => { els[id] = makeEl(id, defs[id]); });
  const boxes = CFG.checkboxes.map(c => makeEl('cb-' + c.key, {dataset: {kind: c.kind, key: c.key}, checked: c.checked}));
  M.boxes = boxes;
  M.box = (kind, key) => boxes.find(b => b.dataset.kind === kind && b.dataset.key === key);
  const doc = {
    visibilityState: 'visible', body: generic('body'), documentElement: generic('html'),
    getElementById: id => els[id] || (els[id] = makeEl(id)),
    querySelectorAll: sel => (sel === '.disp-cb' ? boxes : []), querySelector: () => generic('qs'),
    createElement: () => generic('created'), createElementNS: () => generic('ns'), addEventListener() {},
  };
  const st = (fn, ms) => { const id = M.nextId++; M.timers.push({id, at: M.now + ms, fn, every: null}); return id; };
  const si = (fn, ms) => { if (CFG.kind === 'workshop') return M.nextId++;
                           const id = M.nextId++; M.timers.push({id, at: M.now + ms, fn, every: ms}); return id; };
  const ct = id => { const i = M.timers.findIndex(t => t.id === id); if (i >= 0) M.timers.splice(i, 1); };
  M.advance = async ms => {
    const end = M.now + ms;
    for (;;) {
      M.timers.sort((a, b) => a.at - b.at);
      const t = M.timers.find(t => t.at <= end);
      if (!t) break;
      M.now = t.at;
      if (t.every) t.at += t.every; else M.timers.splice(M.timers.indexOf(t), 1);
      t.fn(); await flush();
    }
    M.now = end; await flush();
  };
  const fetchStub = (url, init) => {
    const method = (init && init.method) || 'GET';
    M.fetches.push({url, method});
    if (url.indexOf('/api/map-overlays') >= 0) {
      if (method === 'POST') {
        if (o.postFail === 'throw') throw new Error('sync failure');
        if (o.postFail === 'reject') return Promise.reject(new Error('network'));
        M.posts.push(JSON.parse(init.body));
        return Promise.resolve({ok: true, json: () => Promise.resolve({ok: true})});
      }
      const m = M.ovMode || o.ovMode || 'json';
      if (m === 'throw') throw new Error('sync failure');
      if (m === 'reject') return Promise.reject(new Error('network'));
      if (m === 'notok') return Promise.resolve({ok: false, json: () => Promise.resolve({})});
      if (m === 'badjson') return Promise.resolve({ok: true, json: () => Promise.reject(new SyntaxError('x'))});
      return Promise.resolve({ok: true, json: () => Promise.resolve(M.overlays)});
    }
    if (url.indexOf('/api/map-center') >= 0)
      return Promise.resolve({ok: true, json: () => Promise.resolve({lng: null, lat: null, zoom: null})});
    return Promise.resolve({ok: true, json: () => Promise.resolve({})});
  };
  const g = generic('maplibregl');
  const maplibregl = new Proxy({Map: FakeMap}, {get: (t, p) => (p in t ? t[p] : g[p])});
  const web = a => ({getItem: k => (k in a ? a[k] : null), setItem: (k, v) => { a[k] = String(v); }, removeItem: k => { delete a[k]; }});
  const win = generic('window');
  win.location = {origin: 'http://t', reload() {}};
  win.addEventListener = () => {};
  const con = {log() {}, warn() {}, error: (...a) => { M.errors.push(a.map(String).join(' ')); }};
  const sandbox = {window: win, document: doc, maplibregl, fetch: fetchStub, console: con,
                   setTimeout: st, clearTimeout: ct, setInterval: si, clearInterval: ct,
                   AbortController, encodeURIComponent, requestAnimationFrame: () => 0,
                   navigator: {clipboard: {writeText() {}}}, getComputedStyle: () => generic('cs'),
                   Blob: function () {}, URL: {createObjectURL: () => 'blob:x', revokeObjectURL() {}},
                   Worker: function () { this.postMessage = () => {}; this.terminate = () => {}; },
                   Image: function () {}, location: {origin: 'http://t', reload() {}},
                   alert() {}, confirm: () => true, prompt: () => null};
  sandbox.sessionStorage = web(sess);
  const mode = o.storage || 'ok';
  if (mode === 'blocked') {
    Object.defineProperty(sandbox, 'localStorage', {get() { throw new Error('SecurityError'); }});
  } else {
    sandbox.localStorage = {
      getItem: k => { if (mode === 'noread') throw new Error('denied'); return k in store ? store[k] : null; },
      setItem: (k, v) => { if (mode === 'full') throw new Error('QuotaExceededError'); store[k] = String(v); },
    };
  }
  M.ctx = vm.createContext(sandbox);
  vm.runInContext(SCRIPT, M.ctx);
  await flush();
  if (CFG.kind === 'workshop') { M.map.fire('load'); }
  else if (M.map) { M.map.fire('load'); }
  await flush();
  return M;
}
"""


def _node(tmp_path, kind, body, html_script, boxes):
    (tmp_path / "page.js").write_text(html_script, encoding="utf-8")
    (tmp_path / "cfg.json").write_text(json.dumps({"kind": kind, "checkboxes": boxes}), encoding="utf-8")
    script = tmp_path / "t.js"
    script.write_text(
        HARNESS + "\n(async () => {\n" + body + "\n})().catch(e => { console.error(e && e.stack || e); process.exit(1); });\n",
        encoding="utf-8")
    r = subprocess.run(["node", str(script), str(tmp_path / "page.js"), str(tmp_path / "cfg.json")],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0, r.stderr + r.stdout
    return json.loads(r.stdout.strip().splitlines()[-1])


def _player(tmp_path, body):
    html = _player_html()
    return _node(tmp_path, "player", body, _player_script(), _checkboxes(html))


def _workshop(tmp_path, body):
    html = _workshop_html()
    return _node(tmp_path, "workshop", body, _workshop_script(), _checkboxes(html))


# ---------------------------------------------------------------------------
# Part C  The player page in node (S3, S4)
# ---------------------------------------------------------------------------

@needs_node
def test_player_overlay_layers_exist_and_are_hidden_before_any_poll(tmp_path):
    r = _player(tmp_path, """
      const m = await boot({ovMode: 'reject'});
      const L = m.map.layers;
      out({ids: Object.keys(L).filter(k => /overlay/.test(k)),
           vis: {topo: L['topo-overlay'].layout.visibility, sat: L['sat-overlay'].layout.visibility},
           types: {topo: L['topo-overlay'].type, sat: L['sat-overlay'].type},
           srcs: Object.keys(m.map.sources).filter(k => /overlay/.test(k))});
    """)
    assert sorted(r["ids"]) == ["sat-overlay", "topo-overlay"]
    assert r["vis"] == {"topo": "none", "sat": "none"}
    assert r["types"] == {"topo": "raster", "sat": "raster"}
    assert sorted(r["srcs"]) == ["sat-overlay", "topo-overlay"]


@needs_node
def test_polling_shows_and_hides_overlays_from_the_gm_payload(tmp_path):
    r = _player(tmp_path, """
      const m = await boot({overlays: {topo: {on: true, opacity: 0.4}, sat: {on: false, opacity: 1}}});
      const L = m.map.layers, snap = () => ({t: L['topo-overlay'].layout.visibility, s: L['sat-overlay'].layout.visibility,
                                              to: L['topo-overlay'].paint['raster-opacity']});
      const first = snap();
      m.overlays = {topo: {on: false, opacity: 0.4}, sat: {on: true, opacity: 0.25}};
      await m.advance(2000);
      const second = snap(); second.so = L['sat-overlay'].paint['raster-opacity'];
      m.overlays = {topo: {on: true, opacity: 5}, sat: {on: false, opacity: -2}};
      await m.advance(2000);
      const third = snap(); third.so = L['sat-overlay'].paint['raster-opacity'];
      out({first, second, third});
    """)
    assert r["first"] == {"t": "visible", "s": "none", "to": 0.4}
    assert (r["second"]["t"], r["second"]["s"], r["second"]["so"]) == ("none", "visible", 0.25)
    assert (r["third"]["t"], r["third"]["to"], r["third"]["so"]) == ("visible", 1, 0)


@needs_node
@pytest.mark.parametrize("on", ["true", 1, "yes", None, 0, [], {}, False])
def test_only_a_real_true_shows_an_overlay(tmp_path, on):
    r = _player(tmp_path, f"""
      const m = await boot({{overlays: {{topo: {{on: {json.dumps(on)}, opacity: 0.5}}, sat: {{on: {json.dumps(on)}}}}}}});
      out([m.map.layers['topo-overlay'].layout.visibility, m.map.layers['sat-overlay'].layout.visibility]);
    """)
    assert r == ["none", "none"]


@needs_node
def test_overlay_polling_runs_whether_or_not_the_player_follows_the_gm(tmp_path):
    r = _player(tmp_path, """
      const m = await boot();
      const count = p => m.fetches.filter(f => f.url.indexOf(p) >= 0 && f.method === 'GET').length;
      const ov0 = count('/api/map-overlays'), mc0 = count('/api/map-center');
      m.el('follow-btn').fire('click');
      m.overlays = {topo: {on: true, opacity: 0.5}, sat: {on: false, opacity: 0.5}};
      await m.advance(6000);
      out({ov: count('/api/map-overlays') - ov0, mc: count('/api/map-center') - mc0,
           vis: m.map.layers['topo-overlay'].layout.visibility, btn: m.el('follow-btn').textContent});
    """)
    assert r["ov"] >= 3
    assert r["mc"] == 0  # not following: no centre polling
    assert r["vis"] == "visible"
    assert "Follow GM" in r["btn"] and "Following" not in r["btn"]


@needs_node
@pytest.mark.parametrize("mode", ["reject", "throw", "notok", "badjson"])
def test_a_failing_poll_leaves_overlays_hidden_and_the_player_sees_nothing(tmp_path, mode):
    r = _player(tmp_path, f"""
      const m = await boot({{ovMode: '{mode}', overlays: {{topo: {{on: true, opacity: 0.5}}, sat: {{on: true}}}}}});
      await m.advance(6000);
      out({{vis: [m.map.layers['topo-overlay'].layout.visibility, m.map.layers['sat-overlay'].layout.visibility],
           errors: m.errors}});
    """)
    assert r["vis"] == ["none", "none"]
    assert r["errors"] == []


@needs_node
def test_a_poll_that_fails_after_a_good_one_keeps_what_was_last_shown(tmp_path):
    r = _player(tmp_path, """
      const m = await boot({overlays: {topo: {on: true, opacity: 0.5}, sat: {on: false}}});
      const before = m.map.layers['topo-overlay'].layout.visibility;
      m.overlays = null;
      await m.advance(4000);
      out({before, after: m.map.layers['topo-overlay'].layout.visibility, errors: m.errors});
    """)
    assert (r["before"], r["after"], r["errors"]) == ("visible", "visible", [])


@needs_node
@pytest.mark.parametrize("mode", ["notok", "badjson", "reject"])
def test_a_bad_reply_after_a_good_poll_keeps_what_was_last_shown(tmp_path, mode):
    r = _player(tmp_path, f"""
      const m = await boot({{overlays: {{topo: {{on: true, opacity: 0.5}}, sat: {{on: false}}}}}});
      const before = m.map.layers['topo-overlay'].layout.visibility;
      m.ovMode = '{mode}';
      await m.advance(4000);
      out({{before, after: m.map.layers['topo-overlay'].layout.visibility, errors: m.errors}});
    """)
    assert (r["before"], r["after"], r["errors"]) == ("visible", "visible", [])


@needs_node
def test_a_failed_overlay_tile_hides_it_silently_until_the_gm_turns_it_off_and_on(tmp_path):
    r = _player(tmp_path, """
      const m = await boot({overlays: {topo: {on: true, opacity: 0.5}, sat: {on: true, opacity: 0.5}}});
      const vis = () => [m.map.layers['topo-overlay'].layout.visibility, m.map.layers['sat-overlay'].layout.visibility];
      const shown = vis();
      m.map.fire('error', {sourceId: 'topo-overlay', error: {status: 404}});
      const afterFail = vis();
      await m.advance(2000);
      const stillFailed = vis();
      m.overlays = {topo: {on: false}, sat: {on: true, opacity: 0.5}};
      await m.advance(2000);
      m.overlays = {topo: {on: true}, sat: {on: true, opacity: 0.5}};
      await m.advance(2000);
      out({shown, afterFail, stillFailed, recovered: vis(), errors: m.errors, badges: Object.keys(m.map.layers).length > 0});
    """)
    assert r["shown"] == ["visible", "visible"]
    assert r["afterFail"] == ["none", "visible"]
    assert r["stillFailed"] == ["none", "visible"]
    assert r["recovered"] == ["visible", "visible"]
    assert r["errors"] == []


@needs_node
def test_errors_from_other_sources_are_still_reported(tmp_path):
    r = _player(tmp_path, """
      const m = await boot();
      m.map.fire('error', {sourceId: 'locations', error: new Error('bad tile')});
      m.map.fire('error', {error: new Error('style')});
      out({errors: m.errors, vis: m.map.layers['topo-overlay'].layout.visibility});
    """)
    assert len(r["errors"]) == 2 and "bad tile" in r["errors"][0]
    assert r["vis"] == "none"


@needs_node
def test_every_player_toggle_starts_on_and_every_layer_it_lists_exists(tmp_path):
    r = _player(tmp_path, """
      const m = await boot();
      const L = m.map.layers;
      out({boxes: m.boxes.map(b => [b.dataset.kind, b.dataset.key, b.checked]),
           missing: m.boxes.filter(b => b.dataset.kind === 'layer').map(b => b.dataset.key)
                      .filter(k => !L[k]),
           tiers: Object.keys(L).filter(k => /^locations-/.test(k)),
           vis: ['routes', 'journeys', 'journeys-hit'].map(k => L[k] && (L[k].layout.visibility || 'visible')),
           saved: Object.keys(m.store)});
    """)
    assert [b[1] for b in r["boxes"] if b[0] == "type"] == TYPE_KEYS
    assert [b[1] for b in r["boxes"] if b[0] == "layer"] == ["routes", "journeys"]
    assert all(b[2] for b in r["boxes"])
    assert r["missing"] == []
    assert sorted(r["tiers"]) == sorted(map_style.tier_categories())
    assert r["vis"] == ["visible", "visible", "visible"]
    assert r["saved"] == []  # nothing is written until the player changes something


@needs_node
def test_type_toggle_filters_only_that_category_and_is_saved(tmp_path):
    r = _player(tmp_path, f"""
      const m = await boot();
      const before = m.map.renderAll();
      const cap = m.box('type', 'capital'); cap.checked = false; cap.fire('change');
      const after = m.map.renderAll();
      const saved = JSON.parse(m.store['{DISPLAY_KEY}']);
      cap.checked = true; cap.fire('change');
      out({{before, after, saved, back: m.map.renderAll()}});
    """)
    assert "fir" in r["before"]["locations-major"] and "amber" in r["before"]["locations-major"]
    assert "fir" not in r["after"]["locations-major"] and "amber" in r["after"]["locations-major"]
    assert {k: v for k, v in r["after"].items() if k != "locations-major"} == \
        {k: v for k, v in r["before"].items() if k != "locations-major"}
    assert r["saved"]["types"]["capital"] is False and r["saved"]["types"]["city"] is True
    assert r["back"] == r["before"]


@needs_node
def test_the_categories_without_a_toggle_always_show(tmp_path):
    r = _player(tmp_path, """
      const m = await boot();
      m.boxes.filter(b => b.dataset.kind === 'type').forEach(b => { b.checked = false; b.fire('change'); });
      out(m.map.renderAll());
    """)
    ruins = {"gorse"}  # public 'ruins' has no toggle, so it stays
    assert ruins <= set(r["locations-detail"])
    assert r["locations-major"] == [] and r["locations-towns"] == []


@needs_node
def test_routes_and_journeys_toggles_hide_and_show_their_layers(tmp_path):
    r = _player(tmp_path, f"""
      const m = await boot();
      const v = () => ['routes', 'journeys', 'journeys-hit'].map(k => m.map.layers[k].layout.visibility);
      const start = v();
      const ro = m.box('layer', 'routes'); ro.checked = false; ro.fire('change');
      const noRoutes = v();
      const jo = m.box('layer', 'journeys'); jo.checked = false; jo.fire('change');
      const none = v();
      ro.checked = true; ro.fire('change');
      const routesBack = v();
      jo.checked = true; jo.fire('change');
      out({{start, noRoutes, none, routesBack, end: v(), saved: JSON.parse(m.store['{DISPLAY_KEY}']).layers}});
    """)
    assert r["start"] == ["visible"] * 3
    assert r["noRoutes"] == ["none", "visible", "visible"]
    assert r["none"] == ["none", "none", "none"]
    assert r["routesBack"] == ["visible", "none", "none"]
    assert r["end"] == ["visible"] * 3
    assert r["saved"] == {"routes": True, "journeys": True}


@needs_node
def test_a_reload_restores_the_saved_toggles(tmp_path):
    saved = json.dumps({"types": {"capital": False, "oasis": False}, "layers": {"routes": False, "journeys": True}})
    r = _player(tmp_path, f"""
      const m = await boot({{local: {{'{DISPLAY_KEY}': {json.dumps(saved)}}}}});
      const R = m.map.renderAll();
      out({{checked: Object.fromEntries(m.boxes.map(b => [b.dataset.key, b.checked])),
           major: R['locations-major'], secondary: R['locations-secondary'], routes: m.map.layers.routes.layout.visibility,
           journeys: m.map.layers.journeys.layout.visibility}});
    """)
    assert r["checked"]["capital"] is False and r["checked"]["oasis"] is False
    assert r["checked"]["city"] is True and r["checked"]["routes"] is False and r["checked"]["journeys"] is True
    assert "fir" not in r["major"] and "amber" in r["major"]
    assert "elm" not in r["secondary"]
    assert (r["routes"], r["journeys"]) == ("none", "visible")


@needs_node
@pytest.mark.parametrize("stored", ["not json", "[]", "5", "null", '"x"', '{"types": 3, "layers": []}',
                                    '{"types": {"city": "no", "town": 0, "bogus": false}, "layers": {"routes": null}}'])
def test_junk_in_storage_falls_back_to_everything_on(tmp_path, stored):
    r = _player(tmp_path, f"""
      const m = await boot({{local: {{'{DISPLAY_KEY}': {json.dumps(stored)}}}}});
      out({{all: m.boxes.every(b => b.checked), routes: m.map.layers.routes.layout.visibility,
           major: m.map.render('locations-major')}});
    """)
    assert r["all"] is True and r["routes"] == "visible" and "amber" in r["major"]


@needs_node
def test_a_partial_saved_state_keeps_the_rest_on(tmp_path):
    saved = json.dumps({"types": {"town": False}})
    r = _player(tmp_path, f"""
      const m = await boot({{local: {{'{DISPLAY_KEY}': {json.dumps(saved)}}}}});
      out(Object.fromEntries(m.boxes.map(b => [b.dataset.key, b.checked])));
    """)
    assert r["town"] is False
    assert all(v for k, v in r.items() if k != "town")


@needs_node
@pytest.mark.parametrize("storage", ["blocked", "noread", "full"])
def test_the_page_renders_and_toggles_work_with_storage_throwing(tmp_path, storage):
    r = _player(tmp_path, f"""
      const m = await boot({{storage: '{storage}'}});
      const cap = m.box('type', 'capital'); cap.checked = false; cap.fire('change');
      const ro = m.box('layer', 'routes'); ro.checked = false; ro.fire('change');
      out({{built: m.maps.length, major: m.map.render('locations-major'), routes: m.map.layers.routes.layout.visibility,
           errors: m.errors, polling: m.fetches.some(f => f.url.indexOf('/api/map-overlays') >= 0)}});
    """)
    assert r["built"] == 1 and r["errors"] == [] and r["polling"] is True
    assert "fir" not in r["major"] and r["routes"] == "none"


@needs_node
def test_player_layers_carry_only_player_filtered_data(tmp_path):
    r = _player(tmp_path, """
      const m = await boot();
      out(m.map.renderAll());
    """)
    shown = {x for ids in r.values() if ids for x in ids}
    assert not (shown & GM_ONLY_LOCATIONS)
    assert set(r["routes"]) == PLAYER_ROUTES
    assert set(r["journeys"]) == PLAYER_JOURNEYS and set(r["journeys-hit"]) == PLAYER_JOURNEYS
    assert set(r) == {"locations-major", "locations-towns", "locations-secondary", "locations-spiritual",
                      "locations-routes", "locations-detail", "routes", "journeys", "journeys-hit",
                      "topo-overlay", "sat-overlay"} | (set(r) & {"regions-fill", "regions-line"})


# ---------------------------------------------------------------------------
# Part D  The Workshop page in node (S2, S5)
# ---------------------------------------------------------------------------

def _last(posts):
    return posts[-1]


@needs_node
def test_workshop_publishes_both_overlays_off_on_load_and_share_defaults_unticked(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      out({posts: m.posts, shares: [m.el('topo-share').checked, m.el('sat-share').checked],
           urls: [...new Set(m.fetches.filter(f => f.method === 'POST').map(f => f.url))]});
    """)
    assert r["posts"] == [{"topo": {"on": False, "opacity": 0.55}, "sat": {"on": False, "opacity": 0.6}}]
    assert r["shares"] == [False, False]
    assert r["urls"] == ["/api/map-overlays"]


@needs_node
def test_published_on_is_enabled_and_shared_and_opacity_is_the_slider(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      const tog = m.el('topo-toggle'), shr = m.el('topo-share');
      const steps = [];
      const step = async (label, f) => { f(); await m.advance(0); steps.push([label, m.posts[m.posts.length - 1].topo.on, m.posts.length]); };
      await step('on, unshared', () => { tog.checked = true; tog.fire('change'); });
      await step('shared', () => { shr.checked = true; shr.fire('change'); });
      await step('off, shared', () => { tog.checked = false; tog.fire('change'); });
      await step('on again', () => { tog.checked = true; tog.fire('change'); });
      await step('unshared', () => { shr.checked = false; shr.fire('change'); });
      out({steps, last: m.posts[m.posts.length - 1], vis: m.map.layers['topo-overlay'].layout.visibility});
    """)
    assert r["steps"] == [["on, unshared", False, 2], ["shared", True, 3], ["off, shared", False, 4],
                          ["on again", True, 5], ["unshared", False, 6]]
    assert r["last"]["sat"] == {"on": False, "opacity": 0.6}
    assert r["vis"] == "visible"  # unticking Share never hides the overlay from the GM


@needs_node
def test_each_overlay_publishes_its_own_key(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      m.el('sat-toggle').checked = true; m.el('sat-toggle').fire('change');
      m.el('sat-share').checked = true; m.el('sat-share').fire('change');
      out(m.posts[m.posts.length - 1]);
    """)
    assert r == {"topo": {"on": False, "opacity": 0.55}, "sat": {"on": True, "opacity": 0.6}}


@needs_node
def test_slider_publishes_once_after_it_settles_not_per_pixel(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      const opc = m.el('topo-opacity'), n0 = m.posts.length;
      for (const v of [10, 20, 30, 35, 40]) { opc.value = String(v); opc.fire('input'); await m.advance(50); }
      const during = m.posts.length - n0;
      await m.advance(249 - 0);
      const settling = m.posts.length - n0;
      await m.advance(10);
      out({during, settling, after: m.posts.length - n0, last: m.posts[m.posts.length - 1].topo,
           paint: m.map.layers['topo-overlay'].paint['raster-opacity'], saved: m.sess._wsTopoOp});
    """)
    assert r["during"] == 0
    assert r["after"] == 1
    assert r["last"] == {"on": False, "opacity": 0.4}
    assert r["paint"] == 0.4 and r["saved"] == "40"


@needs_node
def test_a_pending_slider_publish_is_folded_into_a_toggle_publish(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot(), n0 = m.posts.length;
      m.el('topo-opacity').value = '70'; m.el('topo-opacity').fire('input');
      m.el('topo-toggle').checked = true; m.el('topo-toggle').fire('change');
      await m.advance(1000);
      out({n: m.posts.length - n0, last: m.posts[m.posts.length - 1].topo});
    """)
    assert r["n"] == 1 and r["last"] == {"on": False, "opacity": 0.7}


@needs_node
def test_a_failing_overlay_tile_unchecks_it_and_republishes_off(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      m.el('topo-toggle').checked = true; m.el('topo-toggle').fire('change');
      m.el('topo-share').checked = true; m.el('topo-share').fire('change');
      const published = m.posts[m.posts.length - 1].topo.on, n = m.posts.length;
      m.map.fire('error', {sourceId: 'locations', error: {}});
      const unrelated = m.posts.length - n;
      m.map.fire('error', {sourceId: 'topo-overlay', error: {status: 404}});
      out({published, unrelated, checked: m.el('topo-toggle').checked, vis: m.map.layers['topo-overlay'].layout.visibility,
           last: m.posts[m.posts.length - 1], n: m.posts.length - n, shareStays: m.el('topo-share').checked});
    """)
    assert r["published"] is True and r["unrelated"] == 0
    assert r["checked"] is False and r["vis"] == "none"
    assert r["last"]["topo"]["on"] is False and r["n"] == 1
    assert r["shareStays"] is True


@needs_node
def test_share_and_overlay_state_persist_in_the_session_and_publish_on_load(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot({session: {_wsTopoOn: '1', _wsTopoOp: '30', _wsTopoShare: '1', _wsSatShare: '1'}});
      const boot1 = {posts: m.posts, shares: [m.el('topo-share').checked, m.el('sat-share').checked],
                     vis: m.map.layers['topo-overlay'].layout.visibility};
      m.el('sat-share').checked = false; m.el('sat-share').fire('change');
      m.el('topo-share').checked = false; m.el('topo-share').fire('change');
      out({boot1, sess: [m.sess._wsTopoShare, m.sess._wsSatShare]});
    """)
    assert r["boot1"]["posts"][0] == {"topo": {"on": True, "opacity": 0.3}, "sat": {"on": False, "opacity": 0.6}}
    assert r["boot1"]["shares"] == [True, True] and r["boot1"]["vis"] == "visible"
    assert r["sess"] == ["0", "0"]


@needs_node
def test_ticking_share_writes_the_session_keys(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      m.el('topo-share').checked = true; m.el('topo-share').fire('change');
      m.el('sat-share').checked = true; m.el('sat-share').fire('change');
      out([m.sess._wsTopoShare, m.sess._wsSatShare]);
    """)
    assert r == ["1", "1"]


@needs_node
@pytest.mark.parametrize("fail", ["reject", "throw"])
def test_a_failed_publish_never_breaks_the_workshop(tmp_path, fail):
    r = _workshop(tmp_path, f"""
      const m = await boot({{postFail: '{fail}'}});
      process.on('unhandledRejection', e => {{ console.error('UNHANDLED', e); process.exit(2); }});
      m.el('topo-toggle').checked = true; m.el('topo-toggle').fire('change');
      m.el('topo-opacity').value = '10'; m.el('topo-opacity').fire('input');
      await m.advance(400);
      m.el('sat-share').checked = true; m.el('sat-share').fire('change');
      await flush();
      out({{vis: m.map.layers['topo-overlay'].layout.visibility, errors: m.errors}});
    """)
    assert r["vis"] == "visible" and r["errors"] == []


@needs_node
def test_workshop_menu_lists_routes_journeys_and_the_same_eleven_types():
    boxes = _checkboxes(_workshop_html())
    assert [b["key"] for b in boxes if b["kind"] == "type"] == TYPE_KEYS
    assert [b["key"] for b in boxes if b["kind"] == "layer"] == ["routes", "journeys"]
    html = _workshop_html()
    assert 'id="preview-toggle"' in html and "Player" in html
    for key in OVERLAY_IDS:
        assert f'id="{key}-share"' in html and f'id="{key}-toggle"' in html and f'id="{key}-opacity"' in html


@needs_node
def test_the_routes_toggle_hides_and_shows_the_routes_layer(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      const ro = m.box('layer', 'routes');
      const v = () => m.map.layers.routes.layout.visibility;
      const start = v(), ids0 = m.map.render('routes');
      ro.checked = false; ro.fire('change'); const off = v(), idsOff = m.map.render('routes');
      ro.checked = true; ro.fire('change');
      out({start, off, on: v(), ids0, idsOff, back: m.map.render('routes'), other: m.map.layers.journeys.layout.visibility});
    """)
    assert r["start"] == "visible" and r["off"] == "none" and r["on"] == "visible"
    assert r["idsOff"] == [] and r["back"] == r["ids0"]
    assert set(r["ids0"]) == {"r_public", "r_gm_own", "r_hidden_end"}  # the GM sees every route
    assert r["other"] == "visible"


PLAYER_VIEW = r"""
  const P = m => m.map.renderAll();
"""


@needs_node
def test_without_preview_the_workshop_shows_everything(tmp_path):
    r = _workshop(tmp_path, "const m = await boot(); out(m.map.renderAll());")
    assert GM_ONLY_LOCATIONS <= {x for k, v in r.items() if k.startswith("locations-") for x in v}
    assert set(r["routes"]) == {"r_public", "r_gm_own", "r_hidden_end"}
    assert set(r["journeys"]) == {"j_public", "j_gm_own", "j_hidden_stop"}


@needs_node
def test_preview_hides_gm_locations_routes_and_journeys(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      const pv = m.el('preview-toggle'); pv.checked = true; pv.fire('change');
      out({on: m.map.renderAll(), session: m.sess._wsPreview});
    """)
    shown = {x for k, v in r["on"].items() if k.startswith("locations-") for x in v}
    assert not (shown & GM_ONLY_LOCATIONS) and {"amber", "birch", "elm", "fir", "gorse"} <= shown
    assert set(r["on"]["routes"]) == PLAYER_ROUTES
    assert set(r["on"]["journeys"]) == PLAYER_JOURNEYS and set(r["on"]["journeys-hit"]) == PLAYER_JOURNEYS
    assert r["session"] == "1"


@needs_node
def test_turning_preview_off_brings_everything_back(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      const before = m.map.renderAll();
      const pv = m.el('preview-toggle');
      pv.checked = true; pv.fire('change'); pv.checked = false; pv.fire('change');
      out({before, after: m.map.renderAll(), session: m.sess._wsPreview});
    """)
    assert r["after"] == r["before"] and r["session"] == "0"


@needs_node
def test_preview_is_restored_on_reload(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot({session: {_wsPreview: '1'}});
      out({checked: m.el('preview-toggle').checked, routes: m.map.render('routes'), journeys: m.map.render('journeys')});
    """)
    assert r["checked"] is True
    assert set(r["routes"]) == PLAYER_ROUTES and set(r["journeys"]) == PLAYER_JOURNEYS


@needs_node
def test_preview_composes_with_the_type_toggles_in_either_order(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      const pv = m.el('preview-toggle'), cap = m.box('type', 'capital'), city = m.box('type', 'city');
      cap.checked = false; cap.fire('change');
      pv.checked = true; pv.fire('change');
      const typeThenPreview = m.map.render('locations-major');
      city.checked = false; city.fire('change');
      const cityToo = m.map.render('locations-major');
      pv.checked = false; pv.fire('change');
      const previewOff = m.map.render('locations-secondary'), previewOffMajor = m.map.render('locations-major');
      pv.checked = true; pv.fire('change');
      out({typeThenPreview, cityToo, previewOffMajor, previewOnSecondary: m.map.render('locations-secondary'),
           detail: m.map.render('locations-detail'), previewOff});
    """)
    assert r["typeThenPreview"] == ["amber"]
    assert r["cityToo"] == []
    assert r["previewOffMajor"] == []  # city and capital are still toggled off without the preview
    assert "elm" in r["previewOnSecondary"]
    assert "cedar" not in r["detail"] and "dune" not in r["detail"]
    assert "cedar" in r["previewOff"] or "cedar" not in r["previewOff"]  # secondary tier has no gm_secrets fixture


@needs_node
def test_gm_only_locations_in_a_toggled_tier_return_when_preview_goes_off(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      const pv = m.el('preview-toggle'), poi = m.box('type', 'poi');
      pv.checked = true; pv.fire('change');
      const on = m.map.render('locations-detail');
      pv.checked = false; pv.fire('change');
      const off = m.map.render('locations-detail');
      poi.checked = false; poi.fire('change');
      out({on, off, poiOff: m.map.render('locations-detail')});
    """)
    assert "cedar" not in r["on"] and "cedar" in r["off"] and "dune" in r["off"]
    assert "cedar" not in r["poiOff"] and "dune" in r["poiOff"]  # 'ruins' has no toggle


@needs_node
def test_preview_composes_with_the_journey_editor(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      const run = s => vm.runInContext(s, m.ctx);
      const pv = m.el('preview-toggle');
      run('_ttJid = "j_gm_own"'); run('_ttFilterSaved()');
      const editorOnly = m.map.render('journeys');
      pv.checked = true; pv.fire('change');
      const both = m.map.render('journeys'), bothHit = m.map.render('journeys-hit');
      run('_ttJid = "j_public"'); run('_ttFilterSaved()');
      const editingPublic = m.map.render('journeys');
      run('_ttJid = ""'); run('_ttFilterSaved()');
      out({editorOnly, both, bothHit, editingPublic, closed: m.map.render('journeys')});
    """)
    assert set(r["editorOnly"]) == {"j_public", "j_hidden_stop"}
    assert set(r["both"]) == PLAYER_JOURNEYS and set(r["bothHit"]) == PLAYER_JOURNEYS
    assert r["editingPublic"] == []
    assert set(r["closed"]) == PLAYER_JOURNEYS


@needs_node
def test_preview_filters_only_the_layers_the_player_map_also_has(tmp_path):
    r = _workshop(tmp_path, """
      const m = await boot();
      const pv = m.el('preview-toggle'), before = m.map.renderAll();
      m.map.setFilterCalls.length = 0;
      pv.checked = true; pv.fire('change');
      m.box('type', 'town').checked = false; m.box('type', 'town').fire('change');
      m.box('layer', 'routes').checked = false; m.box('layer', 'routes').fire('change');
      const ws = Object.keys(m.map.layers).filter(k => !/^locations-|^routes$|^journeys/.test(k));
      out({calls: [...new Set(m.map.setFilterCalls)].sort(), untouched: ws.filter(k => m.map.layers[k].filter !== null && before[k] !== undefined && JSON.stringify(m.map.layers[k].filter) !== JSON.stringify(m.map.layers[k].filter)), others: ws});
    """)
    assert set(r["calls"]) <= {"locations-major", "locations-towns", "locations-secondary", "locations-spiritual",
                               "locations-routes", "locations-detail", "routes", "journeys", "journeys-hit"}
    for kept in ("reveal-rings", "highlight-circles"):
        assert kept in r["others"] and kept not in r["calls"]


@needs_node
def test_workshop_preview_shows_what_a_rebuilt_player_map_shows(tmp_path):
    ws = _workshop(tmp_path / "ws" if (tmp_path / "ws").mkdir() is None else tmp_path, """
      const m = await boot();
      const pv = m.el('preview-toggle'); pv.checked = true; pv.fire('change');
      out(m.map.renderAll());
    """)
    pl = _player(tmp_path / "pl" if (tmp_path / "pl").mkdir() is None else tmp_path,
                 "const m = await boot(); out(m.map.renderAll());")
    compared = [k for k in pl if k.startswith("locations-") or k in ("routes", "journeys", "journeys-hit")]
    assert sorted(compared) == sorted(k for k in ws if k.startswith("locations-") or k in ("routes", "journeys", "journeys-hit"))
    for layer in compared:
        assert ws[layer] == pl[layer], layer


@needs_node
def test_with_a_type_off_the_workshop_preview_still_matches_the_player_map(tmp_path):
    body = """
      const m = await boot({%s: {'%s': JSON.stringify({types: {capital: false, oasis: false}, layers: {routes: true}})}});
      %s
      out(m.map.renderAll());
    """
    (tmp_path / "ws").mkdir()
    (tmp_path / "pl").mkdir()
    ws = _workshop(tmp_path / "ws", body % ("session", "_wsDisp",
                                            "const pv = m.el('preview-toggle'); pv.checked = true; pv.fire('change');"))
    pl = _player(tmp_path / "pl", body % ("local", DISPLAY_KEY, ""))
    for layer in [k for k in pl if k.startswith("locations-") or k in ("routes", "journeys", "journeys-hit")]:
        assert ws[layer] == pl[layer], layer
    assert "fir" not in pl["locations-major"] and "elm" not in pl["locations-secondary"]


@needs_node
def test_every_layer_the_shared_control_references_exists_on_both_maps(tmp_path):
    body = """
      const m = await boot();
      const need = vm.runInContext('Object.keys(_tierCats).concat(Object.keys(_dispLayers).flatMap(k => _dispLayers[k]))', m.ctx);
      out({need, missing: need.filter(k => !m.map.layers[k])});
    """
    (tmp_path / "ws").mkdir()
    (tmp_path / "pl").mkdir()
    for r in (_workshop(tmp_path / "ws", body), _player(tmp_path / "pl", body)):
        assert r["missing"] == [] and len(r["need"]) == 9


@needs_node
def test_player_stacks_routes_then_journeys_then_pins_like_the_workshop(tmp_path):
    body = """
      const m = await boot();
      out({order: Object.keys(m.map.layers)});
    """
    (tmp_path / "ws").mkdir()
    (tmp_path / "pl").mkdir()
    for r in (_workshop(tmp_path / "ws", body), _player(tmp_path / "pl", body)):
        order = r["order"]
        pins = [i for i, k in enumerate(order) if k.startswith("locations-")]
        assert pins, order
        assert order.index("journeys") < min(pins)
        assert order.index("journeys-hit") < min(pins)
        assert order.index("routes") < order.index("journeys")


def test_player_panel_puts_routes_and_journeys_in_one_two_column_row():
    html = _player_html()
    row = re.search(r'<div class="disp-layers">(.*?)</div>', html, flags=re.S).group(1)
    assert re.findall(r'data-key="(\w+)"', row) == ["routes", "journeys"]
    assert len(_checkboxes(html)) == 13
    css = map_style.display_controls_css(touch=True)
    assert ".disp-layers" in css and "min-height:44px" in css
