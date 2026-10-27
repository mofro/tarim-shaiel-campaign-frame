"""
Tests for the terrain path worker (#312).

utilities/world/terrain_path.js is evaluated in a Node `vm` context, so the pure
functions (grid planning, A*, path statistics, simplification, routeLeg with a fake
tile provider) run for real without a browser. The browser-only parts (IndexedDB,
fetch, createImageBitmap) sit behind the importScripts check and are covered by
the Workshop verification, not here.
"""

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

from shared import travel_time as tt

WORKER = Path(__file__).parent.parent / "utilities" / "world" / "terrain_path.js"

pytestmark = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")

HARNESS = r"""
const vm = require("vm"), fs = require("fs");
// indexedDB.open returns a request that never fires, like a pending deleteDatabase would
const ctx = vm.createContext({ console, Date, JSON, Promise, setTimeout, clearTimeout,
  indexedDB: { open: function () { return {}; } } });
vm.runInContext(fs.readFileSync(process.argv[2], "utf8"), ctx, { filename: "terrain_path.js" });
const cfg = JSON.parse(process.argv[3]);
ctx.CFG = cfg;
Promise.resolve(vm.runInContext(process.argv[4], ctx)).then(
  r => { console.log(JSON.stringify(r)); },
  e => { console.log(JSON.stringify({ __error: true, code: e.code, message: e.message })); }
);
"""


def run_js(expr: str, cfg: dict | None = None):
    """Evaluate `expr` (an expression, may be a Promise) inside terrain_path.js's scope."""
    cfg = cfg if cfg is not None else json.loads(tt.tt_json())["terrain"]
    r = subprocess.run(
        ["node", "-e", HARNESS, "x", str(WORKER), json.dumps(cfg), expr],
        capture_output=True, text=True, timeout=120,
    )
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout.strip().splitlines()[-1])


def haversine(a, b):
    return tt._haversine_km(a[0], a[1], b[0], b[1])


# --- file hygiene ------------------------------------------------------------

def test_worker_source_parses():
    r = subprocess.run(["node", "--check", str(WORKER)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_worker_source_is_safe_inside_a_script_tag():
    src = WORKER.read_text(encoding="utf-8")
    assert "</" not in src
    assert "<!--" not in src


# --- Tobler factor parity with the Python model ------------------------------

@pytest.mark.parametrize("slope", [-0.6, -0.2, -0.05, 0.0, 0.05, 0.12, 0.35, 0.6])
def test_tobler_factor_matches_python(slope):
    js = run_js(f"toblerFactor({slope}, CFG.toblerK, CFG.toblerOffset)")
    assert js == pytest.approx(tt.tobler_factor(slope), rel=1e-12)


def test_flat_ground_is_unit_speed_and_downhill_is_fastest_at_minus_offset():
    assert tt.tobler_factor(0.0) == pytest.approx(1.0)
    best = max((s / 1000 for s in range(-300, 300)), key=tt.tobler_factor)
    assert best == pytest.approx(-tt.TOBLER_OFFSET, abs=1e-3)
    assert tt.tobler_factor(0.3) < tt.tobler_factor(0.1) < 1.0


def test_terrarium_decoding():
    # sea level is R=128, G=0, B=0
    assert run_js("terrariumMetres(128, 0, 0)") == 0
    assert run_js("terrariumMetres(128, 10, 128)") == pytest.approx(10.5)
    assert run_js("terrariumMetres(127, 255, 0)") == pytest.approx(-1)


# --- Grid selection ------------------------------------------------------------

SAMARKAND = (66.9597, 39.6542)
BUKHARA = (64.4209, 39.7747)
KASHGAR = (75.9892, 39.4677)
LONDON = (-0.1276, 51.5072)
TOKYO = (139.6917, 35.6895)


def plan(a, b, **cfg_over):
    cfg = {**json.loads(tt.tt_json())["terrain"], **cfg_over}
    return run_js(f"planGrid({json.dumps(a)}, {json.dumps(b)}, CFG)", cfg)


def test_short_leg_gets_the_finest_zoom():
    g = plan(SAMARKAND, (SAMARKAND[0] + 0.1, SAMARKAND[1]))
    assert g["z"] == tt.TERRAIN_MAX_ZOOM


def test_long_leg_still_fits_the_cell_cap():
    g = plan(SAMARKAND, KASHGAR)
    assert g is not None
    assert g["cells"] <= tt.TERRAIN_MAX_CELLS
    assert tt.TERRAIN_MIN_ZOOM <= g["z"] <= tt.TERRAIN_MAX_ZOOM


def test_leg_too_large_even_at_min_zoom_is_refused():
    assert plan(LONDON, TOKYO) is None


def test_target_cells_lowers_the_zoom_without_changing_the_refusal_rule():
    big = plan(SAMARKAND, KASHGAR)
    small = plan(SAMARKAND, KASHGAR, targetCells=1_000_000)
    assert small["cells"] <= 1_000_000
    assert small["z"] < big["z"]
    # the refusal rule stays maxCells at minZoom
    assert plan(LONDON, TOKYO, targetCells=1_000_000) is None


# --- A* on synthetic grids ---------------------------------------------------------

def astar_case(w, h, elev_expr, start, goal, mode):
    """Run astar over a w*h grid of 100 m cells with elevation given by a JS expression
    of (x, y). Returns path cells (list of [x, y]) or None, plus steepest step."""
    limit = tt.MAX_SLOPE[mode]
    expr = f"""(function() {{
      var w = {w}, h = {h};
      var elev = new Float32Array(w * h);
      for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) elev[y * w + x] = ({elev_expr});
      var rows = new Float64Array(h).fill(100);
      var p = astar(elev, w, h, rows, {start[0]}, {start[1]}, {goal[0]}, {goal[1]},
                    {limit}, CFG.toblerK, CFG.toblerOffset, function () {{}});
      if (!p) return null;
      var st = pathStats(p, elev, w, rows, CFG.toblerK, CFG.toblerOffset);
      return {{ cells: Array.from(p).map(function (i) {{ return [i % w, Math.floor(i / w)]; }}),
               steepest: st.steepest, lenM: st.lenM, costM: st.costM }};
    }})()"""
    return run_js(expr)


def test_flat_ground_path_is_a_straight_run():
    r = astar_case(40, 20, "0", (2, 10), (37, 10), "foot")
    assert r["cells"][0] == [2, 10] and r["cells"][-1] == [37, 10]
    assert r["lenM"] == pytest.approx(35 * 100)
    assert r["costM"] == pytest.approx(r["lenM"])  # slope 0 -> factor 1


def test_wall_forces_a_detour_through_the_gap():
    # a 10 km-high wall across column 20 with a gap at row 30
    wall = "(x === 20 && y !== 30) ? 10000 : 0"
    r = astar_case(40, 40, wall, (5, 5), (35, 5), "foot")
    assert [20, 30] in r["cells"]
    assert r["steepest"] <= tt.MAX_SLOPE["foot"]


def test_each_mode_respects_its_own_slope_limit():
    # a 30 m step is 0.30 rise/run on 100 m cells: foot (0.6) and mounted (0.35) cross, cart (0.12) cannot
    ridge = "(x >= 18 && x <= 22) ? 30 : 0"
    foot = astar_case(40, 20, ridge, (2, 10), (37, 10), "foot")
    mounted = astar_case(40, 20, ridge, (2, 10), (37, 10), "mounted")
    cart = astar_case(40, 20, ridge, (2, 10), (37, 10), "cart")
    assert foot is not None and mounted is not None
    assert cart is None  # a full-height ridge and no gap


def test_cart_takes_the_gentle_way_round():
    # same ridge, but rows 0-2 stay flat; the cart must use them and never exceed 0.12
    ridge = "(x >= 18 && x <= 22 && y > 2) ? 30 : 0"
    cart = astar_case(40, 20, ridge, (2, 10), (37, 10), "cart")
    assert cart is not None
    assert cart["steepest"] <= tt.MAX_SLOPE["cart"]
    assert any(y <= 2 for _, y in cart["cells"])
    foot = astar_case(40, 20, ridge, (2, 10), (37, 10), "foot")
    assert len(cart["cells"]) >= len(foot["cells"])


def test_start_equal_to_goal():
    r = astar_case(10, 10, "0", (4, 4), (4, 4), "foot")
    assert r["cells"] == [[4, 4]]


def test_path_stats_cost_matches_the_python_model():
    # a uniform 0.05 rise/run climb along one row of 100 m cells
    expr = """(function () {
      var w = 30, h = 3, elev = new Float32Array(w * h);
      for (var y = 0; y < h; y++) for (var x = 0; x < w; x++) elev[y * w + x] = 5 * x;
      var rows = new Float64Array(h).fill(100);
      var path = []; for (var x = 0; x < w; x++) path.push(w + x);
      return pathStats(path, elev, w, rows, CFG.toblerK, CFG.toblerOffset);
    })()"""
    st = run_js(expr)
    assert st["lenM"] == pytest.approx(29 * 100)
    assert st["costM"] / st["lenM"] == pytest.approx(1 / tt.tobler_factor(0.05), rel=1e-6)
    assert st["steepest"] == pytest.approx(0.05)


# --- Simplification ---------------------------------------------------------------

def test_collinear_points_collapse_to_the_ends():
    pts = [[i, 2 * i] for i in range(10)]
    flat = [v for p in pts for v in p]
    assert run_js(f"simplifyIdx({json.dumps(flat)}, 0.6)") == [0, 9]


def test_a_corner_survives_simplification():
    pts = [[0, 0], [5, 0], [10, 0], [10, 5], [10, 10]]
    flat = [v for p in pts for v in p]
    assert run_js(f"simplifyIdx({json.dumps(flat)}, 0.6)") == [0, 2, 4]


# --- routeLeg with a fake tile provider ----------------------------------------------

def route(a, b, mode="foot", provider="flat", cfg_over=None):
    cfg = {**json.loads(tt.tt_json())["terrain"], **(cfg_over or {})}
    providers = {
        "flat": "async function (z, x, y, st) { st.net++; return new Float32Array(65536); }",
        "down": "async function (z, x, y, st) { throw Object.assign(new Error('Could not reach the elevation tile server'), { code: 'network' }); }",
    }
    expr = f"""(function () {{
      var msgs = [];
      var req = {{ id: 7, from: {json.dumps(a)}, to: {json.dumps(b)},
                  maxSlope: {tt.MAX_SLOPE[mode]}, cfg: CFG }};
      return routeLeg(req, {providers[provider]}, function (m) {{ msgs.push(m.phase || m.type); }})
        .then(function (r) {{ r.phases = Array.from(new Set(msgs)); return r; }});
    }})()"""
    return run_js(expr, cfg)


def test_flat_leg_stays_within_the_eight_neighbour_bound_of_the_straight_line():
    a, b = SAMARKAND, (SAMARKAND[0] + 0.9, SAMARKAND[1] + 0.2)
    r = route(a, b)
    assert r["coords"][0] == list(a) and r["coords"][-1] == list(b)
    km = tt.line_length_km(r["coords"])
    straight = haversine(a, b)
    # an 8-neighbour walk is never shorter than the straight line and at most
    # 1/cos(22.5deg) = 8.2% longer (the grid direction nearest the bearing)
    assert straight * 0.999 <= km <= straight * 1.083
    assert r["pathKm"] == pytest.approx(km, rel=0.01)
    # flat ground: cost equals length, so the slope factor is 1
    assert r["costKm"] == pytest.approx(r["pathKm"], rel=1e-6)
    assert r["steepest"] == 0
    assert "tiles" in r["phases"]
    assert r["tilesNet"] > 0 and r["tilesCache"] == 0


def test_same_leg_twice_gives_identical_geometry():
    a, b = SAMARKAND, (SAMARKAND[0] + 0.9, SAMARKAND[1] + 0.2)
    first, second = route(a, b), route(a, b)
    for r in (first, second):
        r.pop("ms")
    assert first == second


def test_a_leg_too_long_to_route_fails_with_a_readable_message():
    r = route(LONDON, TOKYO)
    assert r["__error"] and r["code"] == "toolarge"
    assert "too long" in r["message"] and "zoom 6" in r["message"]


def test_unreachable_tile_server_reports_a_network_error():
    r = route(SAMARKAND, (SAMARKAND[0] + 0.5, SAMARKAND[1]), provider="down")
    assert r["__error"] and r["code"] == "network"
    assert "elevation tile server" in r["message"]


def test_fliers_have_no_slope_limit():
    assert tt.max_slope("bird") is None and tt.max_slope("dragon") is None
    assert tt.max_slope("foot") > tt.max_slope("mounted") > tt.max_slope("cart")


def test_terrain_leg_into_a_closed_cart_valley_reports_no_path():
    # every tile is a 4 km-high wall column pattern: alternate pixels are 4 km up, so no step is passable
    expr = """(function () {
      var req = { id: 1, from: [66.0, 40.0], to: [66.05, 40.0], maxSlope: 0.12, cfg: CFG };
      var prov = async function (z, x, y, st) {
        var t = new Float32Array(65536);
        for (var i = 0; i < t.length; i++) t[i] = (i % 2) ? 4000 : 0;
        return t;
      };
      return routeLeg(req, prov, function () {});
    })()"""
    r = run_js(expr)
    assert r["__error"] and r["code"] == "nopath"
    assert "slope limit" in r["message"]


def test_a_stuck_tile_cache_does_not_hang_routing():
    # the cache open never settles; the worker must give up on it and go to the network
    r = run_js("tileGet('9/1/1').then(function (v) { return { value: v }; })")
    assert r == {"value": None}
