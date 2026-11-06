"""
Tests for the Fantasy Town Generator overlay (#385): the georeference transform, the
trim to what the map draws, the player filter, and the skips.

Scenarios S1-S6 of the issue. The live render (S7) is checked in a browser.
"""

import hashlib
import json
import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities" / "world"))
sys.path.insert(0, str(ROOT / "utilities"))

import generate_map_workshop as gmw
from geojson import settlement_overlay as so
from shared import map_style

CITIES = ROOT / "world" / "maps" / "cities"
EMPTY = {"type": "FeatureCollection", "features": []}

ANCHOR_LAT, ANCHOR_LON = 36.6622, 66.9953

# sha256 of the files as downloaded from FTG on 2026-11-05 (S6).
DEHDADI_SHA256 = {
    "Dehdadi.geojson": "173cdf41e264a5dce7690911537245c05b5a331048294bb55cbb216004dddfcf",
    "Dehdadi.json": "69300e8f3204dd706ab71d6b5085d174e2b4dade5bd5cc2c8dd6e995a5a18f49",
}


def loc(slug, lat=ANCHOR_LAT, lon=ANCHOR_LON, visibility="public"):
    return {"slug": slug, "title": slug.title(), "visibility": visibility, "lat": lat, "lon": lon}


def ftg(*features):
    return {"type": "FeatureCollection", "features": list(features)}


def building(i, ring, btype="RESIDENCE", name="The Test Residence"):
    return {"type": "Feature",
            "properties": {"id": i, "type": "BUILDING", "name": name, "buildingType": btype,
                           "material": "WOOD"},
            "geometry": {"type": "Polygon", "coordinates": [ring]}}


def edge(i, etype, pts):
    return {"type": "Feature",
            "properties": {"id": i, "type": "EDGE", "edgeType": etype},
            "geometry": {"type": "LineString", "coordinates": pts}}


SQUARE = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]


@pytest.fixture(scope="module")
def dehdadi():
    return json.loads((CITIES / "Dehdadi.geojson").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def dehdadi_features(dehdadi):
    return so.build_town_overlay(dehdadi, ANCHOR_LAT, ANCHOR_LON)


# --- S1: georeference ---------------------------------------------------------

def test_metres_per_degree_matches_verified_figures():
    m_lat, m_lon = so.metres_per_degree(ANCHOR_LAT)
    assert m_lat == pytest.approx(110971.3, abs=0.5)
    assert m_lon == pytest.approx(89403.8, abs=0.5)


def test_constants_follow_the_anchor_latitude():
    # Not hard-coded: the equator has a degree of longitude near 111.3 km.
    assert so.metres_per_degree(0.0)[1] == pytest.approx(111319.5, abs=1)
    assert so.metres_per_degree(60.0)[1] == pytest.approx(55800.5, abs=1)


def test_origin_maps_to_anchor_and_axes_point_east_and_north():
    ref = so.Georeference(ANCHOR_LAT, ANCHOR_LON)
    assert ref.to_lonlat(0, 0) == [ANCHOR_LON, ANCHOR_LAT]
    lon, lat = ref.to_lonlat(1000, 0)
    assert lon == pytest.approx(ANCHOR_LON + 1000 / 89403.85, abs=1e-6)
    assert lat == ANCHOR_LAT
    lon, lat = ref.to_lonlat(0, 1000)
    assert lon == ANCHOR_LON
    assert lat == pytest.approx(ANCHOR_LAT + 1000 / 110971.3, abs=1e-6)


@pytest.mark.parametrize("x,y", [(0, 0), (1000, 0), (0, 1000), (-1873.4, 1522.9), (412.25, -1999.9)])
def test_round_trip_within_20_cm(x, y):
    ref = so.Georeference(ANCHOR_LAT, ANCHOR_LON)
    back = ref.to_local(*ref.to_lonlat(x, y))
    assert math.hypot(back[0] - x, back[1] - y) < 0.2


def test_distances_survive_the_transform():
    # 1000 m east and 1000 m north must come out ~1000 m apart on the sphere.
    ref = so.Georeference(ANCHOR_LAT, ANCHOR_LON)
    east = ref.to_lonlat(1000, 0)
    north = ref.to_lonlat(0, 1000)
    assert gmw.haversine_km(ANCHOR_LON, ANCHOR_LAT, *east) == pytest.approx(1.0, abs=0.003)
    assert gmw.haversine_km(ANCHOR_LON, ANCHOR_LAT, *north) == pytest.approx(1.0, abs=0.003)


# --- S2: content --------------------------------------------------------------

def test_invisible_edges_and_background_are_dropped():
    out = so.build_town_overlay(ftg(
        building(1, SQUARE),
        edge(2, "INVISIBLE", [[0, 0], [5, 5]]),
        edge(3, "ROAD", [[0, 0], [5, 5]]),
        {"type": "Feature", "properties": {"id": 4, "type": "BACKGROUND", "backgroundType": "GRASS"},
         "geometry": {"type": "Polygon", "coordinates": [SQUARE]}},
        {"type": "Feature", "properties": {"id": 5, "type": "WATER"},
         "geometry": {"type": "Polygon", "coordinates": [SQUARE]}},
    ), ANCHOR_LAT, ANCHOR_LON)
    assert sorted(f["properties"]["id"] for f in out) == [1, 3, 5]


def test_only_listed_properties_survive():
    out = so.build_town_overlay(ftg(building(1, SQUARE)), ANCHOR_LAT, ANCHOR_LON)
    assert set(out[0]["properties"]) <= set(so.KEPT_PROPERTIES)
    assert "material" not in out[0]["properties"]


def test_dehdadi_counts(dehdadi_features):
    kinds = {}
    for f in dehdadi_features:
        kinds[f["properties"]["type"]] = kinds.get(f["properties"]["type"], 0) + 1
    assert kinds == {"BUILDING": 1629, "EDGE": 1125, "WATER": 1}
    assert not any(f["properties"].get("edgeType") == "INVISIBLE" for f in dehdadi_features)


def test_dehdadi_properties_are_clean(dehdadi_features):
    seen = set()
    for f in dehdadi_features:
        seen |= set(f["properties"])
    assert seen <= set(so.KEPT_PROPERTIES)


def test_dehdadi_lands_around_its_anchor(dehdadi_features):
    lons = [c[0] for f in dehdadi_features for r in _rings(f) for c in r]
    lats = [c[1] for f in dehdadi_features for r in _rings(f) for c in r]
    assert min(lons) < ANCHOR_LON < max(lons)
    assert min(lats) < ANCHOR_LAT < max(lats)
    # The export is +-2000 m: nothing may land more than 2.1 km from the anchor.
    far = max(gmw.haversine_km(ANCHOR_LON, ANCHOR_LAT, lon, lat) for lon, lat in zip(lons, lats))
    assert far < 2.9  # a +-2000 m square has its corner 2.83 km out


def _rings(feature):
    g = feature["geometry"]
    return g["coordinates"] if g["type"] == "Polygon" else [g["coordinates"]]


# --- S3: player filter --------------------------------------------------------

def _town(tmp_path, stem, visibility):
    (tmp_path / f"{stem}.geojson").write_text(json.dumps(ftg(building(1, SQUARE))), encoding="utf-8")
    return loc(stem.lower(), visibility=visibility)


def test_gm_secrets_town_is_absent_from_the_player_copy(tmp_path):
    secret = _town(tmp_path, "Hidden", "gm_secrets")
    public = _town(tmp_path, "Open", "public")
    towns = so.build_overlays([secret, public], tmp_path)
    assert [t["slug"] for t in towns] == ["hidden", "open"]
    assert [t["slug"] for t in so.player_towns(towns)] == ["open"]
    assert len(so.feature_collection(towns)["features"]) == 2
    assert len(so.feature_collection(so.player_towns(towns))["features"]) == 1


def test_player_rule_matches_the_pin_rule(tmp_path):
    # One rule for pins and town maps: same input, same verdict.
    for vis in ("public", "gm_secrets"):
        pin = gmw._player_locations_geojson(
            {"type": "FeatureCollection", "features": [{"properties": {"visibility": vis}}]})
        towns = [{"slug": "x", "visibility": vis, "features": [1]}]
        assert bool(pin["features"]) == bool(so.player_towns(towns))


def test_built_player_page_carries_no_gm_town():
    towns = so.build_overlays([loc("dehdadi", visibility="gm_secrets")])
    html = gmw._build_player_html(
        loc_geojson=EMPTY, routes_geojson=EMPTY, maptiler_key="k",
        settlements_geojson=so.feature_collection(so.player_towns(towns)))
    # Booleans, not `in html`: a failing containment assert makes pytest print the page.
    assert ("Dehdadi School" in html) is False
    assert ("var _settleGJ = " in html) is True


def test_built_gm_page_carries_the_town():
    towns = so.build_overlays([loc("dehdadi", visibility="gm_secrets")])
    html = gmw._build_html(EMPTY, EMPTY, EMPTY, [], [], "", "k",
                           settlements_geojson=so.feature_collection(towns))
    assert ("Dehdadi School" in html) is True
    assert ('map.addSource("settlements"' in html) is True


def test_main_gives_players_only_the_public_town(tmp_path, monkeypatch):
    # The wiring in main(): the GM page gets every town, the player page the public ones.
    cities = tmp_path / "cities"
    cities.mkdir()
    for stem, hall in (("Hidden", "Hidden Hall"), ("Open", "Open Hall")):
        (cities / f"{stem}.geojson").write_text(
            json.dumps(ftg(building(1, SQUARE, name=hall))), encoding="utf-8")

    def page(slug, visibility):
        return {**loc(slug, visibility=visibility), "fantasy_name": "", "description": "",
                "location_type": "city", "status": "canon", "parent_region": "",
                "map_label": None, "map_marker": None}

    real = so.build_overlays
    monkeypatch.setattr(gmw, "MAPTILER_KEY", "k")
    monkeypatch.setattr(gmw, "load_all_locations",
                        lambda _d: [page("hidden", "gm_secrets"), page("open", "public")])
    monkeypatch.setattr(gmw.settlement_overlay, "build_overlays", lambda locs: real(locs, cities))
    for name in ("ROUTES_PATH", "REGIONS_PATH", "JOURNEYS_PATH"):
        monkeypatch.setattr(gmw, name, tmp_path / "absent.geojson")
    monkeypatch.setattr(gmw, "OUTPUT_PATH", tmp_path / "gm.html")
    monkeypatch.setattr(gmw, "PLAYER_PATH", tmp_path / "player.html")

    assert gmw.main() == 0
    gm = (tmp_path / "gm.html").read_text(encoding="utf-8")
    player = (tmp_path / "player.html").read_text(encoding="utf-8")
    seen = lambda page: ("Hidden Hall" in page, "Open Hall" in page)
    assert seen(gm) == (True, True)
    assert seen(player) == (False, True)


def test_layer_ids_constant_matches_the_layers_emitted():
    js = map_style.settlements_layers_js()
    emitted = [json.loads(line[len("map.addLayer("):-2])["id"] for line in js.splitlines()]
    assert emitted == map_style.SETTLEMENT_LAYER_IDS


def _town_layers():
    js = map_style.settlements_layers_js()
    return {layer["id"]: layer for layer in
            (json.loads(line[len("map.addLayer("):-2]) for line in js.splitlines())}


def test_town_fades_in_between_zoom_10_and_12():
    layers = _town_layers()
    for layer in layers.values():
        paint = layer["paint"]
        opacity = paint.get("fill-opacity", paint.get("line-opacity"))
        assert opacity[:3] == ["interpolate", ["linear"], ["zoom"]]
        assert opacity[3:6] == [10, 0, 12]
    assert {layers[i]["minzoom"] for i in map_style.SETTLEMENT_LAYER_IDS[:-1]} == {10}
    assert layers["settlements-building-lines"]["minzoom"] == 12


def test_town_line_widths_are_anchored_at_zoom_13_not_at_the_fade_start():
    layers = _town_layers()
    for layer_id in ("settlements-walls", "settlements-roads"):
        width = layers[layer_id]["paint"]["line-width"]
        assert width[:3] == ["interpolate", ["exponential", 2], ["zoom"]]
        assert width[3::2] == [13, 18]


def test_layers_sit_under_routes_and_pins():
    html = gmw._build_html(EMPTY, EMPTY, EMPTY, [], [], "", "k")
    order = [html.index(s) for s in ('addSource("settlements"', 'addSource("routes"',
                                      'addSource("locations"')]
    assert order == sorted(order)
    player = gmw._build_player_html(loc_geojson=EMPTY, routes_geojson=EMPTY, maptiler_key="k")
    order = [player.index(s) for s in ("addSource('settlements'", "addSource('routes'",
                                       "addSource('locations'")]
    assert order == sorted(order)


# --- S4: skips ----------------------------------------------------------------

def test_town_without_a_page_is_skipped_with_a_warning(tmp_path, capsys):
    _town(tmp_path, "Orphan", "public")
    assert so.build_overlays([loc("other")], tmp_path) == []
    assert "Orphan.geojson has no location page" in capsys.readouterr().err


def test_page_without_coordinates_is_skipped_with_a_warning(tmp_path, capsys):
    page = _town(tmp_path, "Nowhere", "public")
    page["lat"] = page["lon"] = None
    assert so.build_overlays([page], tmp_path) == []
    assert "no coordinates" in capsys.readouterr().err


def test_match_ignores_case_of_the_file_stem(tmp_path):
    page = _town(tmp_path, "MixedCase", "public")
    assert page["slug"] == "mixedcase"
    assert len(so.build_overlays([page], tmp_path)) == 1


# --- S5: size -----------------------------------------------------------------

def test_dehdadi_overlay_stays_under_700_kb():
    towns = so.build_overlays([loc("dehdadi")])
    compact = gmw._settlements_json(so.feature_collection(towns))
    assert len(compact.encode("utf-8")) <= 700_000


# --- S6: sources untouched ----------------------------------------------------

@pytest.mark.parametrize("name", sorted(DEHDADI_SHA256))
def test_source_files_are_byte_identical_to_the_downloads(name):
    assert hashlib.sha256((CITIES / name).read_bytes()).hexdigest() == DEHDADI_SHA256[name]


def test_people_file_never_reaches_the_page(dehdadi_features):
    people = json.loads((CITIES / "Dehdadi.json").read_text(encoding="utf-8"))
    assert people  # the people file exists and is not empty
    blob = json.dumps(dehdadi_features)
    # Every key the overlay may carry is in KEPT_PROPERTIES; no person field is among them.
    assert not (set(so.KEPT_PROPERTIES) & {"people", "families", "residents", "occupants"})
    assert '"people"' not in blob and '"families"' not in blob
