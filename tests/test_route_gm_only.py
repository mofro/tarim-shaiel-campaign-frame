"""
Tests for GM-only routes outside the Workshop page (#310): the public locations
build, the devserver PATCH endpoint, and the route writers that must keep a
route's `visibility` and `mode`.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities"))
sys.path.insert(0, str(ROOT / "utilities" / "routes"))

import devserver
import add_route
import generate_routes
from locations import generate_locations_html as gl

A = (70.0, 40.0)
B = (71.0, 40.0)


def fc(*features):
    return {"type": "FeatureCollection", "features": list(features)}


def route(rid, **props):
    return {"type": "Feature", "id": rid, "properties": props,
            "geometry": {"type": "LineString", "coordinates": [list(A), list(B)]}}


def loc(slug, lonlat, visibility):
    return {"slug": slug, "title": slug.title(), "fantasy_name": "", "description": "",
            "location_type": "town", "visibility": visibility, "status": "draft",
            "parent_region": None, "lat": lonlat[1], "lon": lonlat[0],
            "map_label": True, "map_marker": None}


# --- public locations build ---------------------------------------------------

@pytest.fixture
def build(monkeypatch, tmp_path):
    """Run gl.generate() on tiny inputs and capture what the page builders receive."""
    seen = {}

    def run(locations, routes, waystations=None, **kwargs):
        data = tmp_path / "data"
        data.mkdir(exist_ok=True)
        (data / "routes.geojson").write_text(json.dumps(routes), encoding="utf-8")
        monkeypatch.setattr(gl, "_ROUTES_GEOJSON", data / "routes.geojson")
        way = data / "waystations.geojson"
        if waystations is not None:
            way.write_text(json.dumps(waystations), encoding="utf-8")
        monkeypatch.setattr(gl, "_WAYSTATIONS_GEOJSON", way)
        monkeypatch.setattr(gl, "_REGIONS_GEOJSON", data / "none.geojson")
        monkeypatch.setattr(gl, "_JOURNEYS_GEOJSON", data / "none-journeys.geojson")
        monkeypatch.setattr(gl, "DOCS_DIR", tmp_path / "docs")
        monkeypatch.setattr(gl, "load_all_locations", lambda *a, **k: locations)
        monkeypatch.setattr(gl, "load_all_regions", lambda *a, **k: {})

        def page(loc_, regions, locs_gj, routes_gj, waystations_gj, gm_mode, **kw):
            seen["page"] = (routes_gj, waystations_gj)
            return "<html></html>"

        def home(locs, regions, locs_gj, routes_gj, regions_gj, waystations_gj, gm_mode, **kw):
            seen["home"] = (routes_gj, waystations_gj)
            return "<html></html>"

        monkeypatch.setattr(gl, "_build_location_page", page)
        monkeypatch.setattr(gl, "_build_world_home", home)
        assert gl.generate(**kwargs) == 0
        return seen

    return run


def route_ids(gj):
    return [f["id"] for f in gj["features"]]


def test_public_build_drops_routes_with_a_hidden_end(build):
    locations = [loc("a", A, "public"), loc("b", B, "gm_secrets")]
    routes = fc(route("r1", visibility="public"))
    seen = build(locations, routes, public_only=True)
    assert route_ids(seen["home"][0]) == []


def test_public_build_drops_gm_only_routes_between_public_ends(build):
    locations = [loc("a", A, "public"), loc("b", B, "public")]
    routes = fc(route("r_gm", visibility="gm_secrets"), route("r_none"))
    seen = build(locations, routes, public_only=True)
    assert route_ids(seen["home"][0]) == []


def test_public_build_keeps_a_public_route_between_public_ends(build):
    locations = [loc("a", A, "public"), loc("b", B, "public")]
    seen = build(locations, fc(route("r1", visibility="public")), public_only=True)
    assert route_ids(seen["home"][0]) == ["r1"]
    assert route_ids(seen["page"][0]) == ["r1"]


def test_public_build_filters_waystations_with_their_route(build):
    locations = [loc("a", A, "public"), loc("b", B, "public")]
    routes = fc(route("r_pub", visibility="public"), route("r_gm", visibility="gm_secrets"))
    way = fc(
        {"type": "Feature", "properties": {"route_segment": "r_pub"},
         "geometry": {"type": "Point", "coordinates": [70.5, 40.0]}},
        {"type": "Feature", "properties": {"route_segment": "r_gm"},
         "geometry": {"type": "Point", "coordinates": [70.6, 40.0]}},
    )
    seen = build(locations, routes, way, public_only=True)
    assert [f["properties"]["route_segment"] for f in seen["home"][1]["features"]] == ["r_pub"]


def test_gm_build_keeps_every_route(build):
    locations = [loc("a", A, "gm_secrets"), loc("b", B, "gm_secrets")]
    routes = fc(route("r_gm", visibility="gm_secrets"), route("r_none"))
    seen = build(locations, routes, gm_mode=True)
    assert route_ids(seen["home"][0]) == ["r_gm", "r_none"]


# --- devserver PATCH ----------------------------------------------------------

@pytest.fixture
def routes_file(monkeypatch, tmp_path):
    gj = fc(route("r1", label="One", stroke="#111", visibility="gm_secrets"),
            route("r2", label="Two", stroke="#222", visibility="gm_secrets"))
    path = tmp_path / "routes.geojson"
    text = json.dumps(gj, indent=2, ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(devserver, "ROUTES_PATH", path)
    return path, text


def changed_lines(before, after):
    return [(a, b) for a, b in zip(before.splitlines(), after.splitlines()) if a != b]


def test_patch_visibility_changes_exactly_one_line(routes_file):
    path, before = routes_file
    status, body = devserver._patch_route_props("r1", {"visibility": "public"})
    assert status == 200 and body["fields"] == {"visibility": "public"}
    after = path.read_text(encoding="utf-8")
    assert changed_lines(before, after) == [
        ('        "visibility": "gm_secrets"', '        "visibility": "public"')]
    assert len(before.splitlines()) == len(after.splitlines())


def test_patch_mode_on_a_route_without_one_adds_one_line(routes_file):
    path, before = routes_file
    status, _ = devserver._patch_route_props("r2", {"mode": "cart"})
    assert status == 200
    after = path.read_text(encoding="utf-8")
    assert len(after.splitlines()) == len(before.splitlines()) + 1
    assert json.loads(after)["features"][1]["properties"]["mode"] == "cart"


def test_patch_leaves_other_routes_alone_and_keeps_the_serialization(routes_file):
    path, before = routes_file
    devserver._patch_route_props("r1", {"visibility": "public"})
    after = json.loads(path.read_text(encoding="utf-8"))
    assert after["features"][1] == json.loads(before)["features"][1]
    # No change at all round-trips byte for byte, with no trailing newline.
    devserver._patch_route_props("r1", {"visibility": "gm_secrets"})
    assert path.read_text(encoding="utf-8") == before


@pytest.mark.parametrize("data", [
    {"visibility": "secret"}, {"visibility": None}, {"mode": "teleport"},
    {"visibility": "public", "mode": "teleport"},
])
def test_patch_rejects_bad_values_without_writing(routes_file, data):
    path, before = routes_file
    status, body = devserver._patch_route_props("r1", data)
    assert status == 400 and body["ok"] is False
    assert path.read_text(encoding="utf-8") == before


def test_patch_ignores_unlisted_fields(routes_file):
    path, before = routes_file
    status, _ = devserver._patch_route_props("r1", {"stroke": "#fff"})
    assert status == 400
    status, body = devserver._patch_route_props("r1", {"visibility": "public", "stroke": "#fff"})
    assert status == 200 and body["fields"] == {"visibility": "public"}
    assert json.loads(path.read_text(encoding="utf-8"))["features"][0]["properties"]["stroke"] == "#111"


def test_patch_unknown_route_is_404(routes_file):
    status, body = devserver._patch_route_props("nope", {"visibility": "public"})
    assert status == 404 and body["ok"] is False


def test_patch_leaves_no_temp_file(routes_file):
    path, _ = routes_file
    devserver._patch_route_props("r1", {"visibility": "public"})
    assert not path.with_suffix(".tmp").exists()


def test_patch_route_is_wired_into_do_patch():
    import inspect
    src = inspect.getsource(devserver._Handler.do_PATCH)
    assert "/api/routes/" in src and "_patch_route" in src


# --- route writers keep visibility and mode -----------------------------------

def test_new_routes_default_to_gm_only():
    feat = add_route._make_feature(
        "route_seg_a_b", "a", "b", {"coords": list(A), "label": "A"},
        {"coords": list(B), "label": "B"}, spur=False)
    assert feat["properties"]["visibility"] == "gm_secrets"
    assert "mode" not in feat["properties"]


def test_new_route_takes_visibility_and_mode():
    feat = add_route._make_feature(
        "route_seg_a_b", "a", "b", {"coords": list(A), "label": "A"},
        {"coords": list(B), "label": "B"}, spur=False, visibility="public", mode="mounted")
    assert feat["properties"]["visibility"] == "public"
    assert feat["properties"]["mode"] == "mounted"


def test_regenerating_a_route_keeps_visibility_and_mode(monkeypatch):
    routed = [list(A), [70.5, 40.1], list(B)]
    monkeypatch.setattr(generate_routes, "osrm_route", lambda *a, **k: routed)
    feat = route("r1", label="One", visibility="public", mode="cart")
    out, status = generate_routes.route_feature(feat, {}, force=True)
    assert status == "routed" and out["geometry"]["coordinates"] == routed
    assert out["properties"] == {"label": "One", "visibility": "public", "mode": "cart"}


def test_resyncing_endpoints_keeps_visibility_and_mode(monkeypatch):
    moved = {"a": (70.5, 40.5), "b": B}
    monkeypatch.setattr(generate_routes, "_location_lonlat", lambda slug: moved.get(slug))
    feat = route("route_seg_a_b", visibility="public", mode="foot")
    out = generate_routes._resync_endpoints(feat)
    assert out["geometry"]["coordinates"][0] == [70.5, 40.5]
    assert out["properties"]["visibility"] == "public" and out["properties"]["mode"] == "foot"
