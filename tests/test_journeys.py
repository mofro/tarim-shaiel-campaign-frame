"""
Tests for saved travel journeys (#311): the store, validation, the player
visibility rule, popup content and the devserver endpoints.
"""

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities"))

import devserver
from shared import journeys, travel_time
from locations import generate_locations_html as gl

A = (70.0, 40.0)
B = (71.0, 40.0)
C = (72.0, 40.0)
FREE = (75.0, 41.0)   # matches no location


def fc(*features):
    return {"type": "FeatureCollection", "features": list(features)}


def loc(slug, lonlat, visibility):
    return {"type": "Feature", "id": f"location_{slug}",
            "properties": {"slug": slug, "visibility": visibility},
            "geometry": {"type": "Point", "coordinates": list(lonlat)}}


def stop(name, lonlat, slug=None):
    s = {"lng": lonlat[0], "lat": lonlat[1], "name": name}
    if slug:
        s["slug"] = slug
    return s


def leg(a, b, mode="foot", path="straight", **extra):
    return {"mode": mode, "path": path, "coords": [list(a), list(b)], **extra}


def body(name="Silk Run", stops=None, legs=None, **extra):
    stops = stops or [stop("A", A, "a"), stop("B", B, "b"), stop("C", C, "c")]
    legs = legs or [leg(A, B, "foot", "road"), leg(B, C, "cart", "straight")]
    return {"name": name, "stops": stops, "legs": legs, **extra}


@pytest.fixture
def store(tmp_path):
    return tmp_path / "journeys.geojson"


# --- store ---------------------------------------------------------------------

def test_a_missing_file_loads_as_an_empty_collection(store):
    assert journeys.load(store) == {"type": "FeatureCollection", "features": []}


def test_three_leg_journey_round_trips(store):
    stops = [stop("A", A, "a"), stop("B", B, "b"), stop("C", C, "c"), stop("Free", FREE)]
    legs = [leg(A, B, "foot", "road"), leg(B, C, "cart", "straight"),
            leg(C, FREE, "mounted", "road")]
    feat = journeys.create(store, body(stops=stops, legs=legs))
    saved = journeys.load(store)["features"][0]
    assert saved == feat
    assert [l["mode"] for l in saved["properties"]["legs"]] == ["foot", "cart", "mounted"]
    assert [l["path"] for l in saved["properties"]["legs"]] == ["road", "straight", "road"]
    assert saved["geometry"]["type"] == "MultiLineString"
    assert saved["geometry"]["coordinates"][2] == [list(C), list(FREE)]
    assert [s["name"] for s in saved["properties"]["stops"]] == ["A", "B", "C", "Free"]


def test_a_new_journey_is_gm_only_with_a_slug_id(store):
    feat = journeys.create(store, body(name="The Jade Road"))
    assert feat["properties"]["visibility"] == "gm_secrets"
    assert feat["id"] == "journey_the-jade-road"


def test_ids_stay_unique_for_a_repeated_name(store):
    ids = [journeys.create(store, body())["id"] for _ in range(3)]
    assert ids == ["journey_silk-run", "journey_silk-run-2", "journey_silk-run-3"]


def test_the_file_has_one_coordinate_pair_per_line_and_a_trailing_newline(store):
    journeys.create(store, body())
    text = store.read_text(encoding="utf-8")
    assert text.endswith("}\n")
    assert "[70.0, 40.0]" in text
    assert json.loads(text)["features"][0]["geometry"]["coordinates"][0] == [[70.0, 40.0], [71.0, 40.0]]


def test_saving_leaves_no_temp_file(store):
    journeys.create(store, body())
    assert not store.with_suffix(".tmp").exists()


def test_a_failed_write_keeps_the_old_file(store, monkeypatch):
    journeys.create(store, body())
    before = store.read_text(encoding="utf-8")

    def boom(*a, **k):
        raise OSError("disk full")

    monkeypatch.setattr(journeys.os, "replace", boom)
    with pytest.raises(OSError):
        journeys.create(store, body(name="Second"))
    assert store.read_text(encoding="utf-8") == before
    assert not store.with_suffix(".tmp").exists()


def test_delete_removes_only_that_feature(store):
    keep = journeys.create(store, body(name="Keep"))
    gone = journeys.create(store, body(name="Gone"))
    assert journeys.delete(store, gone["id"]) is True
    assert [f["id"] for f in journeys.load(store)["features"]] == [keep["id"]]
    assert journeys.load(store)["features"][0] == keep


def test_delete_of_an_unknown_id_changes_nothing(store):
    journeys.create(store, body())
    before = store.read_text(encoding="utf-8")
    assert journeys.delete(store, "journey_nope") is False
    assert store.read_text(encoding="utf-8") == before


def test_replace_keeps_id_created_date_and_visibility(store):
    feat = journeys.create(store, body(name="Old", visibility="public"))
    feat["properties"]["created"] = "2026-01-02"
    journeys.save(store, fc(feat))
    new_legs = [leg(A, B, "mounted", "road"), leg(B, C, "mounted", "road")]
    out = journeys.replace(store, feat["id"], body(name="New", legs=new_legs))
    assert out["id"] == feat["id"]
    assert out["properties"]["name"] == "New"
    assert out["properties"]["visibility"] == "public"
    assert out["properties"]["created"] == "2026-01-02"
    assert [l["mode"] for l in out["properties"]["legs"]] == ["mounted", "mounted"]
    assert len(journeys.load(store)["features"]) == 1


def test_replace_of_an_unknown_id_is_none(store):
    assert journeys.replace(store, "journey_nope", body()) is None
    assert not store.exists()


def test_patch_changes_only_name_and_visibility(store):
    feat = journeys.create(store, body())
    out = journeys.patch(store, feat["id"], {"name": "Renamed", "visibility": "public"})
    assert out["properties"]["name"] == "Renamed"
    assert out["properties"]["visibility"] == "public"
    assert out["geometry"] == feat["geometry"]
    assert out["properties"]["legs"] == feat["properties"]["legs"]
    assert out["id"] == feat["id"]


def test_patch_ignores_other_fields_and_rejects_an_empty_change(store):
    feat = journeys.create(store, body())
    with pytest.raises(journeys.JourneyError):
        journeys.patch(store, feat["id"], {"legs": []})
    with pytest.raises(journeys.JourneyError):
        journeys.patch(store, feat["id"], {})


def test_patch_of_an_unknown_id_is_none(store):
    assert journeys.patch(store, "journey_nope", {"name": "x"}) is None


# --- validation ----------------------------------------------------------------

def broken(**changes):
    data = body()
    data.update(changes)
    return data


@pytest.mark.parametrize("data", [
    None, [], "journey",
    broken(name=""), broken(name="   "),
    broken(stops=[stop("A", A)], legs=[]),                       # one stop
    broken(legs=[leg(A, B)]),                                     # legs != stops - 1
    broken(stops="no"), broken(legs="no"),
    broken(legs=[leg(A, B, mode="teleport"), leg(B, C)]),
    broken(legs=[leg(A, B, path="river"), leg(B, C)]),
    broken(legs=[{"mode": "foot", "path": "road", "coords": [list(A)]}, leg(B, C)]),
    broken(legs=[{"mode": "foot", "path": "road", "coords": "no"}, leg(B, C)]),
    broken(legs=[{"mode": "foot", "path": "road", "coords": [[70.0], [71.0, 40.0]]}, leg(B, C)]),
    broken(legs=[leg(A, B, slope_factor=0), leg(B, C)]),
    broken(legs=[leg(A, B, slope_factor=True), leg(B, C)]),
    broken(stops=[stop("A", (200.0, 40.0)), stop("B", B), stop("C", C)]),
    broken(stops=[stop("A", A, "../etc"), stop("B", B), stop("C", C)]),
    broken(visibility="secret"),
])
def test_bad_bodies_are_refused_without_writing(store, data):
    with pytest.raises(journeys.JourneyError):
        journeys.create(store, data)
    assert not store.exists()


def test_too_many_stops_are_refused(store):
    n = journeys.MAX_STOPS + 1
    stops = [stop(f"S{i}", (70.0 + i * 0.01, 40.0)) for i in range(n)]
    legs = [leg((70.0 + i * 0.01, 40.0), (70.0 + (i + 1) * 0.01, 40.0)) for i in range(n - 1)]
    with pytest.raises(journeys.JourneyError):
        journeys.create(store, body(stops=stops, legs=legs))


def test_an_oversized_leg_is_refused(store):
    coords = [[70.0 + i * 1e-5, 40.0] for i in range(journeys.MAX_LEG_POINTS + 1)]
    legs = [{"mode": "foot", "path": "road", "coords": coords}, leg(B, C)]
    with pytest.raises(journeys.JourneyError):
        journeys.create(store, body(legs=legs))


def test_derived_fields_in_the_body_are_ignored(store):
    feat = journeys.create(store, body(id="journey_evil", created="1999-01-01",
                                       geometry={"type": "Point", "coordinates": [0, 0]}))
    assert feat["id"] == "journey_silk-run"
    assert feat["properties"]["created"] != "1999-01-01"
    assert feat["geometry"]["type"] == "MultiLineString"


def test_slope_factor_is_kept_on_the_leg(store):
    legs = [leg(A, B, "foot", "terrain", slope_factor=0.75), leg(B, C)]
    feat = journeys.create(store, body(legs=legs))
    assert feat["properties"]["legs"][0]["slope_factor"] == 0.75
    assert "slope_factor" not in feat["properties"]["legs"][1]


def test_names_are_trimmed_and_capped(store):
    feat = journeys.create(store, body(name="  " + "x" * 500 + "  "))
    assert feat["properties"]["name"] == "x" * journeys.MAX_NAME


# --- times ---------------------------------------------------------------------

def test_a_leg_time_follows_its_own_mode_and_path(store):
    feat = journeys.create(store, body())
    km0, km1 = journeys.leg_km(feat, 0), journeys.leg_km(feat, 1)
    assert journeys.leg_hours(feat, 0) == pytest.approx(travel_time.segment_hours(km0, "foot", "road"))
    assert journeys.leg_hours(feat, 1) == pytest.approx(travel_time.segment_hours(km1, "cart", "straight"))
    assert journeys.summary(feat)["total_hours"] == pytest.approx(
        journeys.leg_hours(feat, 0) + journeys.leg_hours(feat, 1))


def test_changing_one_legs_mode_changes_only_that_leg(store):
    before = journeys.create(store, body())
    legs = [leg(A, B, "foot", "road"), leg(B, C, "mounted", "straight")]
    after = journeys.replace(store, before["id"], body(legs=legs))
    assert journeys.leg_hours(after, 0) == pytest.approx(journeys.leg_hours(before, 0))
    assert journeys.leg_hours(after, 1) < journeys.leg_hours(before, 1)
    assert after["geometry"]["coordinates"][0] == before["geometry"]["coordinates"][0]


def test_a_flier_ignores_the_leg_path(store):
    walk = journeys.create(store, body(legs=[leg(A, B, "bird", "road"), leg(B, C, "bird", "road")]))
    cut = journeys.create(store, body(legs=[leg(A, B, "bird", "straight"), leg(B, C, "bird", "straight")]))
    assert journeys.leg_hours(walk, 0) == pytest.approx(journeys.leg_hours(cut, 0))


def test_popup_info_is_pre_formatted_strings(store):
    feat = journeys.create(store, body())
    info = journeys.popup_info(feat)
    assert info["name"] == "Silk Run"
    assert [r["from"] for r in info["legs"]] == ["A", "B"]
    assert [r["to"] for r in info["legs"]] == ["B", "C"]
    assert info["legs"][0]["how"] == "Foot, road"
    assert info["legs"][1]["how"] == "Cart, straight line"
    assert all(isinstance(v, str) for r in info["legs"] for v in r.values())
    assert " km" in info["total"] and info["total"].count("·") == 1


def test_a_flying_leg_names_no_path_in_the_popup(store):
    feat = journeys.create(store, body(legs=[leg(A, B, "dragon", "road"), leg(B, C, "foot", "road")]))
    assert journeys.popup_info(feat)["legs"][0]["how"] == "Dragon"


# --- player visibility ---------------------------------------------------------

def public(feat):
    feat["properties"]["visibility"] = "public"
    return feat


def made(store, **kw):
    return journeys.create(store, body(**kw))


def test_a_gm_only_journey_never_reaches_players(store):
    feat = made(store)
    locs = fc(loc("a", A, "public"), loc("b", B, "public"), loc("c", C, "public"))
    assert journeys.visible_journeys(fc(feat), locs)["features"] == []


def test_a_public_journey_over_public_stops_is_visible(store):
    feat = public(made(store))
    locs = fc(loc("a", A, "public"), loc("b", B, "public"), loc("c", C, "public"))
    assert [f["id"] for f in journeys.visible_journeys(fc(feat), locs)["features"]] == [feat["id"]]


@pytest.mark.parametrize("hidden", ["a", "b", "c"])
def test_any_hidden_stop_hides_a_public_journey(store, hidden):
    feat = public(made(store))
    locs = fc(*[loc(s, p, "gm_secrets" if s == hidden else "public")
                for s, p in (("a", A), ("b", B), ("c", C))])
    assert journeys.visible_journeys(fc(feat), locs)["features"] == []


def test_a_stop_is_matched_by_position_even_without_a_slug(store):
    stops = [stop("A", A), stop("B", B)]
    feat = public(journeys.create(store, body(stops=stops, legs=[leg(A, B)])))
    locs = fc(loc("a", A, "gm_secrets"), loc("b", B, "public"))
    assert journeys.visible_journeys(fc(feat), locs)["features"] == []


def test_a_stop_whose_location_is_gone_hides_the_journey(store):
    feat = public(made(store))
    locs = fc(loc("a", A, "public"), loc("c", C, "public"))   # "b" no longer exists
    assert journeys.visible_journeys(fc(feat), locs)["features"] == []


def test_free_points_are_allowed(store):
    stops = [stop("Camp", FREE), stop("Ridge", (75.5, 41.0))]
    feat = public(journeys.create(store, body(stops=stops, legs=[leg(FREE, (75.5, 41.0))])))
    assert len(journeys.visible_journeys(fc(feat), fc(loc("a", A, "gm_secrets")))["features"]) == 1


def test_the_location_id_form_of_a_slug_is_understood(store):
    feat = public(made(store))
    locs = fc({**loc("a", A, "gm_secrets"), "properties": {"visibility": "gm_secrets"}},
              loc("b", B, "public"), loc("c", C, "public"))
    assert journeys.visible_journeys(fc(feat), locs)["features"] == []


def test_a_missing_or_malformed_visibility_fails_closed(store):
    feat = made(store)
    locs = fc(loc("a", A, "public"), loc("b", B, "public"), loc("c", C, "public"))
    for value in (None, "", "Public", "secret"):
        feat["properties"]["visibility"] = value
        assert journeys.visible_journeys(fc(feat), locs)["features"] == []
    del feat["properties"]["visibility"]
    assert journeys.visible_journeys(fc(feat), locs)["features"] == []


def test_no_journeys_gives_an_empty_collection():
    assert journeys.visible_journeys(None, None)["features"] == []
    assert journeys.visible_journeys(fc(), fc())["features"] == []


def test_annotate_marks_what_players_can_see(store):
    shown = public(made(store, name="Shown"))
    hidden = made(store, name="Hidden")
    locs = fc(loc("a", A, "public"), loc("b", B, "public"), loc("c", C, "public"))
    out = journeys.annotate_player_visible(fc(shown, hidden), locs)
    assert {f["properties"]["name"]: f["properties"]["_playerVisible"] for f in out["features"]} == {
        "Shown": True, "Hidden": False}


def test_player_payload_exposes_only_name_geometry_and_popup_text(store):
    feat = public(made(store))
    locs = fc(loc("a", A, "public"), loc("b", B, "public"), loc("c", C, "public"))
    gj, info = journeys.player_payload(fc(feat), locs)
    assert list(info) == [feat["id"]]
    out = gj["features"][0]
    assert out["properties"] == {"id": feat["id"], "name": "Silk Run"}
    dumped = json.dumps([gj, info])
    for secret in ("gm_secrets", "visibility", "slug", "created", "updated"):
        assert secret not in dumped


# --- devserver endpoints -------------------------------------------------------

@pytest.fixture
def journeys_file(monkeypatch, tmp_path):
    path = tmp_path / "journeys.geojson"
    monkeypatch.setattr(devserver, "JOURNEYS_PATH", path)
    return path


def test_endpoint_helpers_map_results_to_status_codes(journeys_file):
    status, out = devserver._journey_create(body())
    assert status == 201 and out["ok"] is True
    jid = out["journey"]["id"]

    status, out = devserver._journey_list()
    assert status == 200 and [f["id"] for f in out["features"]] == [jid]

    status, out = devserver._journey_replace(jid, body(name="Again"))
    assert status == 200 and out["journey"]["properties"]["name"] == "Again"

    status, out = devserver._journey_patch(jid, {"visibility": "public"})
    assert status == 200 and out["journey"]["properties"]["visibility"] == "public"

    status, out = devserver._journey_delete(jid)
    assert status == 200 and out["ok"] is True
    assert devserver._journey_list()[1]["features"] == []


def test_endpoint_helpers_report_bad_input_and_missing_ids(journeys_file):
    assert devserver._journey_create({"name": ""})[0] == 400
    assert devserver._journey_replace("journey_nope", body())[0] == 404
    assert devserver._journey_patch("journey_nope", {"name": "x"})[0] == 404
    assert devserver._journey_patch("journey_nope", {"bogus": 1})[0] == 400
    assert devserver._journey_delete("journey_nope")[0] == 404
    assert not journeys_file.exists()


def test_a_bad_request_leaves_the_file_untouched(journeys_file):
    devserver._journey_create(body())
    before = journeys_file.read_text(encoding="utf-8")
    assert devserver._journey_create(body(legs=[leg(A, B, mode="teleport"), leg(B, C)]))[0] == 400
    assert journeys_file.read_text(encoding="utf-8") == before


def test_journey_routes_are_wired_into_the_handler():
    import inspect
    for method, helper in (("do_GET", "_journey_list"), ("do_POST", "_journey_create"),
                           ("do_PUT", "_journey_replace"), ("do_PATCH", "_journey_patch"),
                           ("do_DELETE", "_journey_delete")):
        src = inspect.getsource(getattr(devserver._Handler, method))
        assert "/api/journeys" in src, method
        assert helper in src or "_handle_journey" in src, method


def test_reading_journeys_is_limited_to_local_clients():
    import inspect
    src = inspect.getsource(devserver._Handler.do_GET)
    start = src.index("/api/journeys")
    assert "_is_local" in src[max(0, start - 200):start + 300]


# --- public locations build ----------------------------------------------------

@pytest.fixture
def build(monkeypatch, tmp_path):
    """Run gl.generate() on tiny inputs and capture the journeys the page builders get."""
    seen = {}

    def run(locations, journeys_gj, **kwargs):
        data = tmp_path / "data"
        data.mkdir(exist_ok=True)
        (data / "journeys.geojson").write_text(json.dumps(journeys_gj), encoding="utf-8")
        monkeypatch.setattr(gl, "_JOURNEYS_GEOJSON", data / "journeys.geojson")
        monkeypatch.setattr(gl, "_ROUTES_GEOJSON", data / "none-routes.geojson")
        monkeypatch.setattr(gl, "_WAYSTATIONS_GEOJSON", data / "none-way.geojson")
        monkeypatch.setattr(gl, "_REGIONS_GEOJSON", data / "none.geojson")
        monkeypatch.setattr(gl, "DOCS_DIR", tmp_path / "docs")
        monkeypatch.setattr(gl, "load_all_locations", lambda *a, **k: locations)
        monkeypatch.setattr(gl, "load_all_regions", lambda *a, **k: {})

        def page(loc_, regions, locs_gj, routes_gj, waystations_gj, gm_mode, **kw):
            seen["page"] = kw.get("journeys")
            return "<html></html>"

        def home(locs, regions, locs_gj, routes_gj, regions_gj, waystations_gj, gm_mode, **kw):
            seen["home"] = kw.get("journeys")
            return "<html></html>"

        monkeypatch.setattr(gl, "_build_location_page", page)
        monkeypatch.setattr(gl, "_build_world_home", home)
        assert gl.generate(**kwargs) == 0
        return seen

    return run


def plain_loc(slug, lonlat, visibility):
    return {"slug": slug, "title": slug.title(), "fantasy_name": "", "description": "",
            "location_type": "town", "visibility": visibility, "status": "draft",
            "parent_region": None, "lat": lonlat[1], "lon": lonlat[0],
            "map_label": True, "map_marker": None}


def two_stop_journey(store, visibility):
    feat = journeys.create(store, body(stops=[stop("A", A, "a"), stop("B", B, "b")],
                                       legs=[leg(A, B)]))
    feat["properties"]["visibility"] = visibility
    return feat


def test_public_build_keeps_a_public_journey_between_public_stops(build, store):
    feat = two_stop_journey(store, "public")
    seen = build([plain_loc("a", A, "public"), plain_loc("b", B, "public")], fc(feat),
                 public_only=True)
    gj, info = seen["home"]
    assert [f["id"] for f in gj["features"]] == [feat["id"]]
    assert feat["id"] in info


def test_public_build_drops_gm_only_and_hidden_stop_journeys(build, store):
    gm = two_stop_journey(store, "gm_secrets")
    seen = build([plain_loc("a", A, "public"), plain_loc("b", B, "public")], fc(gm),
                 public_only=True)
    assert seen["home"][0]["features"] == [] and seen["page"][0]["features"] == []
    pub = two_stop_journey(store, "public")
    seen = build([plain_loc("a", A, "public"), plain_loc("b", B, "gm_secrets")], fc(pub),
                 public_only=True)
    assert seen["home"][0]["features"] == []


def test_gm_build_keeps_every_journey(build, store):
    gm = two_stop_journey(store, "gm_secrets")
    seen = build([plain_loc("a", A, "gm_secrets"), plain_loc("b", B, "gm_secrets")], fc(gm),
                 gm_mode=True)
    assert [f["id"] for f in seen["home"][0]["features"]] == [gm["id"]]


# --- map pages ---------------------------------------------------------------

def test_map_pages_build_without_journey_arguments():
    from world import generate_map_workshop as gmw
    html = gmw._build_player_html(loc_geojson=fc(), routes_geojson=fc(), maptiler_key="k")
    assert 'var _journeyGJ = {"type": "FeatureCollection", "features": []};' in html
    assert "var _jrnInfo = {};" in html


def test_workshop_loads_saved_journeys_from_the_devserver_on_boot():
    from world import generate_map_workshop as gmw
    assert 'fetch("/api/journeys")' in gmw._TRAVEL_JS
