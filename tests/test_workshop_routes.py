"""
Tests for GM-only routes and route travel time in the Map Workshop (#310):
the route index uses the shared speed table, the route panel and the app JS
agree on element ids, and the player map only ever receives routes that the
visibility rule lets through.
"""

import inspect
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities" / "world"))
sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

import generate_map_workshop as gmw
from shared import map_style, route_visibility, travel_time

A = (70.0, 40.0)
B = (71.0, 40.0)   # ~85 km east of A at this latitude


def loc(slug, lonlat, visibility):
    return {"type": "Feature", "id": f"location_{slug}",
            "properties": {"slug": slug, "visibility": visibility},
            "geometry": {"type": "Point", "coordinates": list(lonlat)}}


def route(rid, visibility, mode=None, mid=None):
    coords = [list(A)] + ([list(mid)] if mid else []) + [list(B)]
    props = {"label": f"label-{rid}", "title": f"SECRET-TITLE-{rid}",
             "description": f"SECRET-DESC-{rid}"}
    if visibility is not None:
        props["visibility"] = visibility
    if mode:
        props["mode"] = mode
    return {"type": "Feature", "id": rid, "properties": props,
            "geometry": {"type": "LineString", "coordinates": coords}}


def fc(*features):
    return {"type": "FeatureCollection", "features": list(features)}


def locs(a="public", b="public"):
    return fc(loc("a", A, a), loc("b", B, b))


def by_id(gj):
    return {f["id"]: f["properties"] for f in gj["features"]}


# --- visibility annotation ---------------------------------------------------

def test_annotate_flags_follow_the_visibility_rule():
    routes = fc(route("r_pub", "public"), route("r_gm", "gm_secrets"))
    p = by_id(gmw.annotate_routes(routes, locs("public", "public")))
    assert p["r_pub"]["_playerVisible"] is True and p["r_pub"]["_endsPublic"] is True
    assert p["r_gm"]["_playerVisible"] is False and p["r_gm"]["_endsPublic"] is True

    held = by_id(gmw.annotate_routes(routes, locs("public", "gm_secrets")))
    assert held["r_pub"]["_playerVisible"] is False
    assert held["r_pub"]["_endsPublic"] is False


def test_annotate_does_not_mutate_the_source():
    routes = fc(route("r1", "public"))
    gmw.annotate_routes(routes, locs())
    assert "_playerVisible" not in routes["features"][0]["properties"]


# --- route time --------------------------------------------------------------

@pytest.mark.parametrize("mode", list(travel_time.SPEEDS))
def test_route_index_time_is_length_over_speed(mode):
    routes = gmw.annotate_routes(fc(route("r1", "public", mode=mode, mid=(70.5, 40.2))), locs())
    row = gmw._build_route_index(routes)[0]
    km = travel_time.line_length_km(routes["features"][0]["geometry"]["coordinates"])
    expected_days = km / travel_time.SPEEDS[mode]["kmpd"]   # road path, 3 points
    assert row["mode"] == mode
    assert row["hours"] / travel_time.MARCH_HOURS == pytest.approx(expected_days)
    assert row["is_approx"] is False


def test_two_point_route_is_a_straight_estimate():
    routes = gmw.annotate_routes(fc(route("r1", "public")), locs())
    row = gmw._build_route_index(routes)[0]
    km = travel_time.line_length_km([list(A), list(B)])
    assert row["is_approx"] is True
    assert row["time"].startswith("~")
    assert row["hours"] / travel_time.MARCH_HOURS == pytest.approx(
        km / (travel_time.SPEEDS["foot"]["kmpd"] * travel_time.PATH_FACTORS["straight"]))


def test_missing_mode_is_foot_and_missing_visibility_is_gm_only():
    routes = gmw.annotate_routes(fc(route("r1", None, mid=(70.5, 40.1))), locs())
    row = gmw._build_route_index(routes)[0]
    assert row["mode"] == "foot"
    assert row["visibility"] == "gm_secrets" and row["player_visible"] is False


def test_index_html_marks_who_sees_each_route():
    routes = gmw.annotate_routes(
        fc(route("r_pub", "public"), route("r_gm", "gm_secrets"), route("r_held", "public")),
        fc(loc("a", A, "public"), loc("b", B, "public")))
    # Make r_held end at a hidden location by giving it a third location as its end.
    html = gmw._route_index_html(gmw._build_route_index(routes))
    assert "30 km/d" not in html
    assert "ri-vis-pub" in html and "ri-vis-gm" in html

    held = gmw.annotate_routes(fc(route("r_held", "public")), locs("public", "gm_secrets"))
    assert "ri-vis-held" in gmw._route_index_html(gmw._build_route_index(held))


# --- shared speed table in the Workshop ---------------------------------------

def test_travel_presets_come_from_the_shared_table():
    html = gmw._build_panel_travel_time()
    for mode, spec in travel_time.SPEEDS.items():
        assert f'data-mode="{mode}" data-kpd="{spec["kmpd"]}" data-fly="{1 if spec["fly"] else 0}"' in html
    assert "__TT_" not in html
    assert f'value="{travel_time.SPEEDS[travel_time.DEFAULT_MODE]["kmpd"]}"' in html


def test_workshop_embeds_the_speed_table():
    src = inspect.getsource(gmw._build_html)
    assert "var _TT = {travel_time.tt_json()}" in src


def test_hidden_routes_are_dimmed_only_when_asked():
    plain = map_style.routes_layer_js()
    dim = map_style.routes_layer_js(dim_hidden=True)
    assert "_playerVisible" not in plain
    assert "_playerVisible" in dim


# --- route panel wiring -------------------------------------------------------

def test_route_panel_ids_used_by_js_are_rendered():
    html_src = inspect.getsource(gmw._build_html)
    rendered = set(re.findall(r'id=\\?"([^"\\]+)\\?"', html_src))
    js = gmw._build_app_js("https://example.test/style.json", "", "")
    wanted = set(re.findall(r'getElementById\("(route-panel[^"]*)"\)', js))
    assert {"route-panel-vis", "route-panel-mode", "route-panel-time", "route-panel-seen"} <= wanted
    assert wanted <= rendered, f"missing: {sorted(wanted - rendered)}"


def test_route_panel_patches_one_property_at_a_time():
    js = gmw._build_app_js("https://example.test/style.json", "", "")
    assert 'method:"PATCH"' in js and '"/api/routes/"+encodeURIComponent(id)' in js
    assert '_patchRoute("visibility",this.value)' in js
    assert '_patchRoute("mode",this.value)' in js


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_app_js_parses(tmp_path):
    js = gmw._build_app_js("https://example.test/style.json", "", "")
    out = tmp_path / "app.js"
    out.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


# --- player map ---------------------------------------------------------------

def test_player_map_never_embeds_gm_only_routes():
    routes = fc(route("r_pub", "public"), route("r_gm", "gm_secrets"), route("r_none", None))
    shown = route_visibility.visible_routes(routes, locs("public", "public"))
    html = gmw._build_player_html(loc_geojson=fc(), routes_geojson=shown, maptiler_key="k")
    assert "SECRET-TITLE-r_pub" in html
    for hidden in ("r_gm", "r_none"):
        assert f"SECRET-TITLE-{hidden}" not in html
        assert f"SECRET-DESC-{hidden}" not in html


def test_player_map_with_a_hidden_end_has_no_routes():
    routes = fc(route("r_pub", "public"))
    shown = route_visibility.visible_routes(routes, locs("public", "gm_secrets"))
    html = gmw._build_player_html(loc_geojson=fc(), routes_geojson=shown, maptiler_key="k")
    assert "SECRET-TITLE-r_pub" not in html
    assert json.loads(re.search(r"var _routeGJ = (\{.*?\});\n", html).group(1))["features"] == []
