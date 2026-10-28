"""
Tests for the player map's start view (#324): the view is chosen before the map is
constructed, so a refresh never shows the default and then eases to the GM.

Order: GM position (GET /api/map-center, short timeout) -> view stored on this
device (localStorage `ts_player_view`) -> default. Most tests run the real emitted
page script in node against stubbed `maplibregl`, `fetch`, `localStorage` and timers.
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

EMPTY = {"type": "FeatureCollection", "features": []}
DEFAULT = gmw.PLAYER_DEFAULT_VIEW
KEY = gmw.PLAYER_VIEW_KEY
TIMEOUT = gmw.PLAYER_GM_VIEW_TIMEOUT_MS


def _player_html():
    return gmw._build_player_html(loc_geojson=EMPTY, routes_geojson=EMPTY, maptiler_key="k")


def _page_script():
    html = _player_html()
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.S)
    return next(s for s in scripts if "_initMap" in s)


# ---------------------------------------------------------------------------
# What the generated page contains
# ---------------------------------------------------------------------------

def test_default_view_is_still_the_one_the_page_always_opened_on():
    assert DEFAULT == {"lng": 70, "lat": 40, "zoom": 4}


def test_start_view_constants_are_emitted_from_the_python_constants():
    page = _page_script()
    assert f"var _VIEW_KEY = {json.dumps(KEY)};" in page
    assert f"var _DEFAULT_VIEW = {json.dumps(DEFAULT)};" in page
    assert f"var _GM_VIEW_TIMEOUT = {TIMEOUT};" in page
    assert KEY == "ts_player_view" and TIMEOUT == 800


def test_map_is_constructed_only_inside_initmap_and_not_with_a_literal_view():
    page = _page_script()
    assert page.count("new maplibregl.Map(") == 1
    init = page.index("function _initMap(")
    assert init < page.index("new maplibregl.Map(") < page.index("function _startPolling(")
    assert "center:[v.lng,v.lat],zoom:v.zoom" in page
    assert "center:[70,40]" not in page
    # the only caller is the callback of the pre-construct fetch
    assert re.findall(r"_initMap\(", page) == ["_initMap(", "_initMap("]
    assert "_fetchGmView(function(gm){ _initMap(_chooseStart(gm)); });" in page


def test_view_is_saved_on_pagehide_and_hidden_not_beforeunload():
    page = _page_script()
    assert "beforeunload" not in page and "unload'" not in page
    assert "window.addEventListener('pagehide', _storeView);" in page
    assert re.search(r"visibilitychange.*?visibilityState==='hidden'\)_storeView\(\)", page, re.S)
    assert "map.on('moveend'" in page and "setTimeout(_storeView, 400)" in page


def test_every_storage_access_sits_in_a_try_block():
    page = _page_script()
    hits = [m.start() for m in re.finditer("localStorage", page)]
    assert hits, "page no longer touches localStorage at all"
    for at in hits:
        enclosing = page[page.rfind("function ", 0, at):at]
        assert "try{" in enclosing, page[max(0, at - 80):at + 40]


# ---------------------------------------------------------------------------
# Behaviour: the emitted script, run in node against stubs
# ---------------------------------------------------------------------------

needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

HARNESS = r"""
const fs = require('fs'), vm = require('vm');
const PAGE = fs.readFileSync(process.argv[2], 'utf8');
const KEY = 'ts_player_view';
const out = x => console.log(JSON.stringify(x));
const flush = async () => { for (let i = 0; i < 5; i++) await new Promise(r => setImmediate(r)); };

// o: stored (raw string), gm (body fetch answers with), fetch ('json'|'reject'|'badjson'|'throw'|'hang'),
//    storage ('ok'|'blocked'|'noread'|'full'), noAbort
async function boot(o) {
  o = o || {};
  const store = {};
  if (o.stored !== undefined) store[KEY] = o.stored;
  const timers = []; let now = 0, nextId = 1;
  const h = {store, maps: [], fetches: [], aborts: 0, errors: [],
             gm: o.gm === undefined ? {lng: null, lat: null, zoom: null} : o.gm};
  const winH = {}, docH = {};

  const st = (fn, ms) => { const id = nextId++; timers.push({id, at: now + ms, fn, every: null}); return id; };
  const si = (fn, ms) => { const id = nextId++; timers.push({id, at: now + ms, fn, every: ms}); return id; };
  const ct = id => { const i = timers.findIndex(t => t.id === id); if (i >= 0) timers.splice(i, 1); };
  h.flush = flush;
  h.advance = async ms => {
    const end = now + ms;
    for (;;) {
      timers.sort((a, b) => a.at - b.at);
      const t = timers.find(t => t.at <= end);
      if (!t) break;
      now = t.at;
      if (t.every) t.at += t.every; else timers.splice(timers.indexOf(t), 1);
      t.fn();
      await flush();
    }
    now = end;
    await flush();
  };

  class FakeMap {
    constructor(opts) { this.opts = opts; this.h = {}; this.eased = [];
      this.center = {lng: opts.center[0], lat: opts.center[1]}; this.zoom = opts.zoom; h.maps.push(this); }
    on(t, f) { (this.h[t] = this.h[t] || []).push(f); }
    addControl() {}
    getCenter() { return this.center; }
    getZoom() { return this.zoom; }
    easeTo(opts) { this.eased.push(opts); }
    fire(t) { (this.h[t] || []).forEach(f => f()); }
  }
  const maplibregl = {Map: FakeMap, NavigationControl: function () {}, ScaleControl: function () {}};

  const doc = {
    visibilityState: 'visible',
    addEventListener: (t, f) => { (docH[t] = docH[t] || []).push(f); },
    getElementById: () => ({addEventListener() {}, classList: {toggle() {}}, textContent: ''}),
    querySelectorAll: () => [],
  };
  const win = {location: {origin: 'http://t'},
               addEventListener: (t, f) => { (winH[t] = winH[t] || []).push(f); }};
  h.doc = doc;
  h.fireWindow = t => (winH[t] || []).forEach(f => f());
  h.fireDocument = t => (docH[t] || []).forEach(f => f());

  const fetchStub = (url, init) => {
    h.fetches.push({url, signal: !!(init && init.signal)});
    const mode = o.fetch || 'json';
    if (mode === 'throw') throw new Error('sync failure');
    if (mode === 'reject') return Promise.reject(new Error('network'));
    if (mode === 'badjson') return Promise.resolve({json: () => Promise.reject(new SyntaxError('not json'))});
    if (mode === 'hang') return new Promise((res, rej) => {
      h.late = body => res({json: () => Promise.resolve(body)});
      if (init && init.signal) init.signal.addEventListener('abort', () => { h.aborts++; rej(new Error('AbortError')); });
    });
    return Promise.resolve({json: () => Promise.resolve(h.gm)});
  };

  const sandbox = {window: win, document: doc, fetch: fetchStub, console, maplibregl,
                   setTimeout: st, clearTimeout: ct, setInterval: si, clearInterval: ct,
                   AbortController: o.noAbort ? undefined : AbortController, encodeURIComponent};
  const ctx = vm.createContext(sandbox);
  const mode = o.storage || 'ok';
  if (mode === 'blocked') {
    Object.defineProperty(sandbox, 'localStorage', {get() { throw new Error('SecurityError'); }});
  } else {
    sandbox.localStorage = {
      getItem: k => { if (mode === 'noread') throw new Error('denied'); return k in store ? store[k] : null; },
      setItem: (k, v) => { if (mode === 'full') throw new Error('QuotaExceededError'); store[k] = String(v); },
    };
  }
  h.ctx = ctx;
  vm.runInContext(PAGE, ctx);
  await flush();
  return h;
}
"""


def _node(tmp_path, body):
    (tmp_path / "page.js").write_text(_page_script(), encoding="utf-8")
    script = tmp_path / "t.js"
    script.write_text(
        HARNESS
        + "\n(async () => {\n" + body + "\n})().catch(e => { console.error(e && e.stack || e); process.exit(1); });\n",
        encoding="utf-8",
    )
    r = subprocess.run(
        ["node", str(script), str(tmp_path / "page.js")], capture_output=True, text=True, timeout=30
    )
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


def _built(result):
    return {"lng": result["center"][0], "lat": result["center"][1], "zoom": result["zoom"]}


@needs_node
def test_map_waits_for_the_gm_fetch_and_gives_up_after_the_timeout(tmp_path):
    r = _node(tmp_path, f"""
        const h = await boot({{fetch: 'hang'}});
        const before = h.maps.length;
        await h.advance({TIMEOUT - 1});
        const justBefore = h.maps.length;
        await h.advance(1);
        out({{before, justBefore, after: h.maps.length, aborts: h.aborts,
              url: h.fetches[0].url, signal: h.fetches[0].signal,
              center: h.maps[0].opts.center, zoom: h.maps[0].opts.zoom}});
    """)
    assert (r["before"], r["justBefore"], r["after"]) == (0, 0, 1)
    assert r["url"] == "/api/map-center" and r["signal"] is True
    assert r["aborts"] == 1
    assert _built(r) == DEFAULT


@needs_node
def test_gm_view_beats_the_stored_view_and_seeds_the_first_poll(tmp_path):
    stored = json.dumps({"lng": 10, "lat": 10, "zoom": 5})
    r = _node(tmp_path, f"""
        const h = await boot({{gm: {{lng: 75.2, lat: 38.1, zoom: 7}}, stored: {json.dumps(stored)}}});
        const m = h.maps[0];
        const seeded = h.ctx._lastCenter;
        const want = vm.runInContext('_viewKey({{lng: 75.2, lat: 38.1, zoom: 7}})', h.ctx);
        h.ctx._startPolling();
        await h.advance(2000);
        const afterSamePoll = m.eased.length;
        h.gm = {{lng: 80, lat: 39, zoom: 6}};
        await h.advance(2000);
        out({{n: h.maps.length, center: m.opts.center, zoom: m.opts.zoom, seeded, want,
              afterSamePoll, eased: m.eased}});
    """)
    assert _built(r) == {"lng": 75.2, "lat": 38.1, "zoom": 7}
    assert r["n"] == 1
    assert r["seeded"] and r["seeded"] == r["want"]
    assert r["afterSamePoll"] == 0, "first poll re-eased to where the map already is"
    assert [e["center"] for e in r["eased"]] == [[80, 39]]


@needs_node
@pytest.mark.parametrize("has_stored", [True, False])
def test_empty_gm_response_falls_through_and_is_never_read_as_0_0(tmp_path, has_stored):
    stored = {"lng": 66.5, "lat": 41.25, "zoom": 6.5}
    arg = json.dumps(json.dumps(stored)) if has_stored else "undefined"
    r = _node(tmp_path, f"""
        const h = await boot({{gm: {{lng: null, lat: null, zoom: null}}, stored: {arg}}});
        out({{n: h.maps.length, center: h.maps[0].opts.center, zoom: h.maps[0].opts.zoom,
              seeded: h.ctx._lastCenter}});
    """)
    assert _built(r) == (stored if has_stored else DEFAULT)
    assert r["seeded"] is None, "no GM position yet, so the first real poll must still ease"


@needs_node
def test_gm_nan_and_partial_responses_are_not_used(tmp_path):
    r = _node(tmp_path, """
        const bodies = [{lng: null, lat: 40, zoom: 5}, {lng: 70, lat: null, zoom: 5}, {lng: 70, lat: 40},
                        {lng: 'x', lat: 40, zoom: 5}, {lng: 70, lat: 40, zoom: null}, null, [], 'x'];
        const res = [];
        for (const gm of bodies) {
          const h = await boot({gm});
          res.push({c: h.maps[0].opts.center, z: h.maps[0].opts.zoom});
        }
        out(res);
    """)
    assert all(x == {"c": [DEFAULT["lng"], DEFAULT["lat"]], "z": DEFAULT["zoom"]} for x in r), r


@needs_node
def test_bad_stored_views_fall_back_to_the_default(tmp_path):
    bad = [
        "not json", "null", "[1,2,3]", '"x"', "{}",
        '{"lng":"70","lat":40,"zoom":4}',
        '{"lng":70,"lat":40}',
        '{"lng":200,"lat":0,"zoom":5}',
        '{"lng":-181,"lat":0,"zoom":5}',
        '{"lng":1e999,"lat":40,"zoom":4}',
        '{"lng":70,"lat":-1e999,"zoom":4}',
        '{"lng":70,"lat":40,"zoom":null}',
    ]
    r = _node(tmp_path, f"""
        const res = [];
        for (const stored of {json.dumps(bad)}) {{
          const h = await boot({{stored}});
          res.push({{stored, c: h.maps[0].opts.center, z: h.maps[0].opts.zoom}});
        }}
        out(res);
    """)
    for x in r:
        assert (x["c"], x["z"]) == ([DEFAULT["lng"], DEFAULT["lat"]], DEFAULT["zoom"]), x["stored"]


@needs_node
def test_stored_view_is_clamped_to_lat_and_zoom_limits(tmp_path):
    lo, hi = gmw.PLAYER_VIEW_ZOOM_RANGE
    cases = [
        ({"lng": 70, "lat": 99, "zoom": 6}, {"lng": 70, "lat": 85, "zoom": 6}),
        ({"lng": 70, "lat": -99, "zoom": 6}, {"lng": 70, "lat": -85, "zoom": 6}),
        ({"lng": 70, "lat": 40, "zoom": 0.5}, {"lng": 70, "lat": 40, "zoom": lo}),
        ({"lng": 70, "lat": 40, "zoom": 30}, {"lng": 70, "lat": 40, "zoom": hi}),
        ({"lng": 70, "lat": 40, "zoom": -2}, {"lng": 70, "lat": 40, "zoom": lo}),
    ]
    r = _node(tmp_path, f"""
        const res = [];
        for (const v of {json.dumps([c[0] for c in cases])}) {{
          const h = await boot({{stored: JSON.stringify(v)}});
          res.push({{center: h.maps[0].opts.center, zoom: h.maps[0].opts.zoom}});
        }}
        out(res);
    """)
    assert [_built(x) for x in r] == [c[1] for c in cases]


@needs_node
def test_gm_view_is_clamped_too(tmp_path):
    r = _node(tmp_path, """
        const h = await boot({gm: {lng: 75, lat: 95, zoom: 40}});
        out({center: h.maps[0].opts.center, zoom: h.maps[0].opts.zoom});
    """)
    assert _built(r) == {"lng": 75, "lat": 85, "zoom": gmw.PLAYER_VIEW_ZOOM_RANGE[1]}


@needs_node
@pytest.mark.parametrize("mode", ["reject", "badjson", "throw"])
def test_a_failed_gm_fetch_falls_through_to_the_stored_view(tmp_path, mode):
    stored = {"lng": 66.5, "lat": 41.25, "zoom": 6.5}
    r = _node(tmp_path, f"""
        const h = await boot({{fetch: {json.dumps(mode)}, stored: {json.dumps(json.dumps(stored))}}});
        out({{n: h.maps.length, center: h.maps[0].opts.center, zoom: h.maps[0].opts.zoom}});
    """)
    assert r["n"] == 1 and _built(r) == stored


@needs_node
def test_a_late_gm_answer_cannot_build_a_second_map(tmp_path):
    r = _node(tmp_path, f"""
        const h = await boot({{fetch: 'hang', noAbort: true}});
        await h.advance({TIMEOUT});
        h.late({{lng: 80, lat: 39, zoom: 6}});
        await h.advance(50);
        out({{n: h.maps.length, center: h.maps[0].opts.center, signal: h.fetches[0].signal}});
    """)
    assert r["n"] == 1
    assert r["center"] == [DEFAULT["lng"], DEFAULT["lat"]]
    assert r["signal"] is False, "no AbortController: fetch must still be called, without a signal"


@needs_node
@pytest.mark.parametrize("storage", ["blocked", "noread", "full"])
def test_map_and_writers_survive_blocked_storage(tmp_path, storage):
    r = _node(tmp_path, f"""
        const h = await boot({{storage: {json.dumps(storage)}}});
        const m = h.maps[0];
        m.fire('moveend');
        await h.advance(400);
        h.fireWindow('pagehide');
        h.doc.visibilityState = 'hidden';
        h.fireDocument('visibilitychange');
        out({{n: h.maps.length, center: m.opts.center, zoom: m.opts.zoom, stored: h.store}});
    """)
    assert r["n"] == 1
    assert _built(r) == DEFAULT
    # "noread" only blocks reads, so the writers still land; the other two block writes
    assert r["stored"] == ({KEY: json.dumps(DEFAULT, separators=(",", ":"))} if storage == "noread" else {})


@needs_node
def test_view_is_written_on_debounced_moveend_pagehide_and_hidden(tmp_path):
    r = _node(tmp_path, """
        const h = await boot();
        const m = h.maps[0];
        const s = () => h.store[KEY] === undefined ? null : JSON.parse(h.store[KEY]);
        const seen = {};
        seen.initial = s();

        m.center = {lng: 71, lat: 41}; m.zoom = 5;
        m.fire('moveend');
        await h.advance(300);
        m.center = {lng: 72, lat: 42}; m.zoom = 6;
        m.fire('moveend');
        await h.advance(399);
        seen.debounced = s();
        await h.advance(1);
        seen.afterMoveend = s();

        m.center = {lng: 73, lat: 43}; m.zoom = 7;
        h.fireWindow('pagehide');
        seen.afterPagehide = s();

        m.center = {lng: 74, lat: 44}; m.zoom = 8;
        h.doc.visibilityState = 'visible';
        h.fireDocument('visibilitychange');
        seen.visible = s();
        h.doc.visibilityState = 'hidden';
        h.fireDocument('visibilitychange');
        seen.hidden = s();
        out(seen);
    """)
    assert r["initial"] is None
    assert r["debounced"] is None, "moveend must be debounced, not written per event"
    assert r["afterMoveend"] == {"lng": 72, "lat": 42, "zoom": 6}
    assert r["afterPagehide"] == {"lng": 73, "lat": 43, "zoom": 7}
    assert r["visible"] == {"lng": 73, "lat": 43, "zoom": 7}, "a visible visibilitychange must not write"
    assert r["hidden"] == {"lng": 74, "lat": 44, "zoom": 8}


@needs_node
def test_a_view_written_by_one_load_is_what_the_next_load_starts_from(tmp_path):
    r = _node(tmp_path, """
        const first = await boot();
        first.maps[0].center = {lng: 68.5, lat: 39.25}; first.maps[0].zoom = 7.5;
        first.fireWindow('pagehide');
        const second = await boot({stored: first.store[KEY]});
        out({center: second.maps[0].opts.center, zoom: second.maps[0].opts.zoom});
    """)
    assert _built(r) == {"lng": 68.5, "lat": 39.25, "zoom": 7.5}


@needs_node
def test_pagehide_before_the_map_exists_writes_nothing(tmp_path):
    r = _node(tmp_path, """
        const h = await boot({fetch: 'hang'});
        h.fireWindow('pagehide');
        out({n: h.maps.length, stored: h.store});
    """)
    assert r == {"n": 0, "stored": {}}


# ---------------------------------------------------------------------------
# Devserver: GET /api/map-center answers cleanly when the GM has not moved yet
# ---------------------------------------------------------------------------

@pytest.fixture
def devserver_url(monkeypatch):
    monkeypatch.setattr(devserver, "_map_center", None)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), devserver._Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def _get(url):
    with urllib.request.urlopen(url, timeout=5) as r:
        return r.status, json.loads(r.read())


def _post(url, body):
    req = urllib.request.Request(
        url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


def test_map_center_is_nulls_not_zeros_before_the_gm_has_moved(devserver_url):
    status, body = _get(devserver_url + "/api/map-center")
    assert status == 200
    assert body == {"lng": None, "lat": None, "zoom": None}


def test_map_center_returns_what_the_gm_last_posted(devserver_url):
    assert _post(devserver_url + "/api/map-center", {"lng": 75.5, "lat": 38.25, "zoom": 6.5}) == 200
    assert _get(devserver_url + "/api/map-center")[1] == {"lng": 75.5, "lat": 38.25, "zoom": 6.5}


def test_a_bad_post_leaves_the_map_center_unset(devserver_url):
    assert _post(devserver_url + "/api/map-center", {"lng": "x", "lat": 1}) == 400
    assert _get(devserver_url + "/api/map-center")[1] == {"lng": None, "lat": None, "zoom": None}
