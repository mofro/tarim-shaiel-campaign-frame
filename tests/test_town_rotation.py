"""
Tests for town rotation (#392): `town_rotation:` on a location page turns its FTG town
map clockwise about `location:`, on both maps, and the Workshop previews a typed angle
before Save.

The live render (the town turning on screen, Save, close/Esc revert) is checked in a
browser; these cover the transform, the page key, the two copies of the transform, the
guard on what Save may write, and what each page carries.
"""

import hashlib
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities" / "world"))
sys.path.insert(0, str(ROOT / "utilities"))

import devserver
import generate_map_workshop as gmw
from geojson import settlement_overlay as so
from locations import location_parser

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")

CITIES = ROOT / "world" / "maps" / "cities"
EMPTY = {"type": "FeatureCollection", "features": []}
LAT, LON = 36.6622, 66.9953


def _ftg(*feats):
    return {"type": "FeatureCollection", "features": list(feats)}


def _building(i, ring):
    return {"type": "Feature",
            "properties": {"id": i, "type": "BUILDING", "name": f"Hall {i}", "buildingType": "RESIDENCE"},
            "geometry": {"type": "Polygon", "coordinates": [ring]}}


def _edge(i, pts):
    return {"type": "Feature", "properties": {"id": i, "type": "EDGE", "edgeType": "ROAD"},
            "geometry": {"type": "LineString", "coordinates": pts}}


TOWN = _ftg(
    _building(1, [[0, 0], [40, 0], [40, 25], [0, 25], [0, 0]]),
    _building(2, [[-300, 120], [-260, 120], [-260, 170], [-300, 170], [-300, 120]]),
    _edge(3, [[-500, -400], [0, 0], [650, 310]]),
)


def _hash(features):
    return hashlib.sha256(json.dumps(features, sort_keys=True).encode()).hexdigest()


def _flat(coords):
    if isinstance(coords[0], (int, float)):
        return [coords]
    return [p for part in coords for p in _flat(part)]


def _points(features):
    return [p for f in features for p in _flat(f["geometry"]["coordinates"])]


def _page(slug="dehdadi", visibility="public", rotation=None, lat=LAT, lon=LON):
    page = {"slug": slug, "title": slug.title(), "visibility": visibility, "lat": lat, "lon": lon}
    if rotation is not None:
        page["town_rotation"] = rotation
    return page


@pytest.fixture(scope="module")
def dehdadi():
    return json.loads((CITIES / "Dehdadi.geojson").read_text(encoding="utf-8"))


# --- the transform ------------------------------------------------------------

@pytest.mark.parametrize("zero", [0, 0.0, 360, -360, 720])
def test_zero_and_full_turns_leave_the_output_bit_identical(zero):
    assert _hash(so.build_town_overlay(TOWN, LAT, LON, zero)) == _hash(so.build_town_overlay(TOWN, LAT, LON))


def test_dehdadi_unrotated_output_is_unchanged_by_the_new_parameter(dehdadi):
    assert _hash(so.build_town_overlay(dehdadi, LAT, LON, 0)) == _hash(so.build_town_overlay(dehdadi, LAT, LON))


def test_a_point_north_of_the_centre_goes_east_at_90_and_west_at_minus_90():
    plain = so.Georeference(LAT, LON)
    for angle, want in ((90, (100, 0)), (-90, (-100, 0)), (180, (0, -100)), (270, (-100, 0))):
        lon, lat = so.Georeference(LAT, LON, angle).to_lonlat(0, 100)
        x, y = plain.to_local(lon, lat)
        assert (x, y) == pytest.approx(want, abs=0.2), angle


def test_clockwise_means_east_turns_to_south():
    plain = so.Georeference(LAT, LON)
    x, y = plain.to_local(*so.Georeference(LAT, LON, 90).to_lonlat(100, 0))
    assert (x, y) == pytest.approx((0, -100), abs=0.2)


def test_the_centre_stays_on_the_page_location_and_distances_are_kept():
    plain = so.Georeference(LAT, LON)
    pts = [(0, 0), (120, 30), (-310, 75), (640, -410), (-5, 900)]
    for angle in (30, 117.5, -45, 359.9):
        ref = so.Georeference(LAT, LON, angle)
        assert ref.to_lonlat(0, 0) == [LON, LAT]
        turned = [plain.to_local(*ref.to_lonlat(x, y)) for x, y in pts]
        for i in range(len(pts)):
            for j in range(i + 1, len(pts)):
                before = math.dist(pts[i], pts[j])
                after = math.dist(turned[i], turned[j])
                assert after == pytest.approx(before, abs=0.4), (angle, i, j)


def test_to_local_is_the_inverse_of_to_lonlat_when_turned():
    ref = so.Georeference(LAT, LON, 63.25)
    for x, y in ((0, 0), (850.5, -120.25), (-1500, 1400)):
        back = ref.to_local(*ref.to_lonlat(x, y))
        assert back == pytest.approx((x, y), abs=0.2)


def test_rotation_turns_every_feature_and_keeps_properties(dehdadi):
    plain = so.build_town_overlay(dehdadi, LAT, LON)
    turned = so.build_town_overlay(dehdadi, LAT, LON, 40)
    assert [f["properties"] for f in turned] == [f["properties"] for f in plain]
    assert _hash(turned) != _hash(plain)


# --- the page key -------------------------------------------------------------

def _write_page(tmp_path, fm_extra):
    p = tmp_path / "dehdadi.md"
    p.write_text("---\ntitle: Dehdadi\ncontent_type: location\nvisibility: public\n"
                 f"location: [{LAT}, {LON}]\n{fm_extra}---\n\nBody.\n", encoding="utf-8")
    return p


@pytest.mark.parametrize("fm,want", [
    ("", 0.0),
    ("town_rotation: 30\n", 30.0),
    ("town_rotation: -12.5\n", -12.5),
    ("town_rotation: 0\n", 0.0),
    ("town_rotation:\n", 0.0),
])
def test_parser_reads_town_rotation_as_a_float(tmp_path, capsys, fm, want):
    data = location_parser.parse_location(_write_page(tmp_path, fm))
    assert data["town_rotation"] == want and isinstance(data["town_rotation"], float)
    assert "WARN" not in capsys.readouterr().err


@pytest.mark.parametrize("fm", [
    "town_rotation: abc\n",
    'town_rotation: "30"\n',
    "town_rotation: true\n",
    "town_rotation: .nan\n",
    "town_rotation: .inf\n",
    "town_rotation: [1, 2]\n",
])
def test_a_value_that_is_not_a_number_warns_and_builds_unrotated(tmp_path, capsys, fm):
    data = location_parser.parse_location(_write_page(tmp_path, fm))
    assert data["town_rotation"] == 0.0
    err = capsys.readouterr().err
    assert "WARN: dehdadi has town_rotation" in err
    assert "drawn unrotated" in err


def test_the_page_value_reaches_the_overlay(tmp_path):
    (tmp_path / "Dehdadi.geojson").write_text(json.dumps(TOWN), encoding="utf-8")
    page = location_parser.parse_location(_write_page(tmp_path, "town_rotation: 30\n"))
    (towns,) = so.build_overlays([page], tmp_path)
    assert towns["rotation"] == 30.0
    assert _hash(towns["features"]) == _hash(so.build_town_overlay(TOWN, LAT, LON, 30))


# --- both maps ----------------------------------------------------------------

def test_a_public_town_turns_identically_on_the_player_map_and_a_secret_one_stays_off(tmp_path):
    for stem in ("Open", "Hidden"):
        (tmp_path / f"{stem}.geojson").write_text(json.dumps(TOWN), encoding="utf-8")
    towns = so.build_overlays([_page("open", rotation=30.0), _page("hidden", "gm_secrets", 30.0)], tmp_path)
    gm = so.feature_collection(towns)
    player = so.feature_collection(so.player_towns(towns))
    assert [t["slug"] for t in so.player_towns(towns)] == ["open"]
    assert len(player["features"]) == len(TOWN["features"]) < len(gm["features"])
    assert _hash(player["features"]) == _hash(so.build_town_overlay(TOWN, LAT, LON, 30))


def test_built_player_page_has_the_turned_town_and_no_preview_machinery(tmp_path):
    (tmp_path / "Open.geojson").write_text(json.dumps(TOWN), encoding="utf-8")
    towns = so.build_overlays([_page("open", rotation=30.0)], tmp_path)
    html = gmw._build_player_html(
        loc_geojson=EMPTY, routes_geojson=EMPTY, maptiler_key="k",
        settlements_geojson=so.feature_collection(so.player_towns(towns)))
    assert ("var _townIdx" in html) is False
    assert ("ef-rot" in html) is False
    assert ("_townGJ" in html) is False
    turned = gmw._settlements_json({"type": "FeatureCollection",
                                    "features": so.build_town_overlay(TOWN, LAT, LON, 30)})
    plain = gmw._settlements_json({"type": "FeatureCollection",
                                   "features": so.build_town_overlay(TOWN, LAT, LON)})
    assert turned != plain
    assert (turned in html) is True


# --- the index the page turns by ---------------------------------------------

def test_town_index_ranges_match_the_feature_collection(tmp_path):
    for stem, feats in (("Aaa", TOWN), ("Bbb", _ftg(_building(9, [[0, 0], [5, 0], [5, 5], [0, 0]]))),
                        ("Ccc", TOWN)):
        (tmp_path / f"{stem}.geojson").write_text(json.dumps(feats), encoding="utf-8")
    towns = so.build_overlays([_page("aaa", rotation=10.0), _page("bbb", lat=30.0, lon=60.0),
                               _page("ccc", rotation=-20.0)], tmp_path)
    flat = so.feature_collection(towns)["features"]
    idx = so.town_index(towns)
    assert [t["slug"] for t in idx] == ["aaa", "bbb", "ccc"]
    assert [t["rotation"] for t in idx] == [10.0, 0.0, -20.0]
    for t, town in zip(idx, towns):
        assert flat[t["start"]:t["start"] + t["count"]] == town["features"]
    assert idx[0]["start"] == 0 and idx[-1]["start"] + idx[-1]["count"] == len(flat)
    m_lat, m_lon = so.metres_per_degree(30.0)
    assert (idx[1]["mLat"], idx[1]["mLon"]) == (m_lat, m_lon)


# --- the JS twin --------------------------------------------------------------

def _node(script):
    script = gmw._EF_DIFF_JS + gmw._TOWN_TURN_JS + script
    # On stdin, not `-e`: the script carries the whole town (~700 KB), and Linux refuses a
    # single argument over 128 KiB (E2BIG), which macOS allows.
    out = subprocess.run([NODE, "-"], input=script, capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def _preview(base_features, idx, angles):
    return _node(
        f"var base={{type:'FeatureCollection',features:{json.dumps(base_features)}}};"
        f"console.log(JSON.stringify(_townGJ(base,{json.dumps(idx)},{json.dumps(angles)}).features));")


def _worst_error_m(a, b, idx):
    m_lat, m_lon = idx["mLat"], idx["mLon"]
    return max(math.hypot((p[0] - q[0]) * m_lon, (p[1] - q[1]) * m_lat)
               for p, q in zip(_points(a), _points(b)))


@pytest.fixture(scope="module")
def town_dir(tmp_path_factory, dehdadi):
    d = tmp_path_factory.mktemp("cities")
    (d / "Dehdadi.geojson").write_text(json.dumps(dehdadi), encoding="utf-8")
    return d


def _built(town_dir, rotation):
    towns = so.build_overlays([_page("dehdadi", rotation=rotation)], town_dir)
    return so.feature_collection(towns)["features"], so.town_index(towns)


@needs_node
@pytest.mark.parametrize("angle", [0, 30, 90, -45, 179.5, 270, 359.9, 400])
def test_js_preview_from_the_unrotated_build_matches_the_python_build(town_dir, angle):
    base, idx = _built(town_dir, 0.0)
    want, _ = _built(town_dir, float(angle))
    got = _preview(base, idx, {"dehdadi": angle})
    assert len(got) == len(want)
    assert [f["properties"] for f in got] == [f["properties"] for f in want]
    assert _worst_error_m(got, want, idx[0]) < 0.3


@needs_node
@pytest.mark.parametrize("built,shown", [(30, 100), (30, 0), (-60, 75.5), (359, 1)])
def test_js_preview_from_a_rotated_build_matches_the_python_build(town_dir, built, shown):
    base, idx = _built(town_dir, float(built))
    want, _ = _built(town_dir, float(shown))
    got = _preview(base, idx, {"dehdadi": shown})
    assert _worst_error_m(got, want, idx[0]) < 0.3


@needs_node
def test_the_saved_angle_shows_the_build_unchanged(town_dir):
    base, idx = _built(town_dir, 30.0)
    assert _preview(base, idx, {"dehdadi": 30}) == base
    assert _preview(base, idx, {}) == base


@needs_node
def test_turning_there_and_back_does_not_drift(town_dir):
    base, idx = _built(town_dir, 0.0)
    first = _preview(base, idx, {"dehdadi": 30})
    for _ in range(3):
        _preview(base, idx, {"dehdadi": 60})
        again = _preview(base, idx, {"dehdadi": 30})
        assert again == first


@needs_node
def test_a_preview_leaves_the_built_data_and_other_towns_alone(tmp_path):
    for stem in ("Aaa", "Bbb"):
        (tmp_path / f"{stem}.geojson").write_text(json.dumps(TOWN), encoding="utf-8")
    towns = so.build_overlays([_page("aaa"), _page("bbb", lat=30.0, lon=60.0)], tmp_path)
    base, idx = so.feature_collection(towns)["features"], so.town_index(towns)
    got = _node(
        f"var base={{type:'FeatureCollection',features:{json.dumps(base)}}};"
        f"var before=JSON.stringify(base);"
        f"var out=_townGJ(base,{json.dumps(idx)},{{aaa:45}});"
        f"console.log(JSON.stringify({{same:JSON.stringify(base)===before,"
        f"n:out.features.length,tail:out.features.slice({idx[1]['start']})}}));")
    assert got["same"] is True
    assert got["n"] == len(base)
    assert got["tail"] == base[idx[1]["start"]:]


@needs_node
@pytest.mark.parametrize("text,want", [
    ("30", 30), ("-12.5", -12.5), ("  7 ", 7), ("", 0), (".5", 0.5), ("+3", 3), ("36000", 36000),
    ("0.12345", 0.1235), ("abc", None), ("1e5", None), ("12abc", None), ("-", None),
    ("36001", None), ("--5", None), ("Infinity", None), ("NaN", None),
])
def test_town_angle_reads_what_the_server_will_accept(text, want):
    got = _node(f"var a=_townAngle({json.dumps(text)});console.log(JSON.stringify(isNaN(a)?null:a));")
    assert got == want


@needs_node
def test_ef_diff_sends_town_rotation_only_when_it_changed():
    base = {"name": "Dehdadi", "town_rotation": "30"}
    assert _node(f"console.log(JSON.stringify(_efDiff({json.dumps(base)},{json.dumps(base)})));") == {}
    cur = {**base, "town_rotation": "45.5"}
    assert _node(f"console.log(JSON.stringify(_efDiff({json.dumps(base)},{json.dumps(cur)})));") \
        == {"town_rotation": 45.5}
    blank = {**base, "town_rotation": ""}
    assert _node(f"console.log(JSON.stringify(_efDiff({json.dumps(base)},{json.dumps(blank)})));") \
        == {"town_rotation": None}


@needs_node
def test_a_page_with_no_town_never_sends_town_rotation():
    base = {"name": "Achal", "visibility": "public"}
    cur = {**base, "visibility": "gm_secrets"}
    assert _node(f"console.log(JSON.stringify(_efDiff({json.dumps(base)},{json.dumps(cur)})));") \
        == {"visibility": "gm_secrets"}


# --- what Save may write ------------------------------------------------------

PAGE = (
    "---\n"
    "title: Dehdadi\n"
    "visibility: gm_secrets\n"
    "last_updated: 2026-10-26\n"
    "location: [36.6622, 66.9953]\n"
    "fantasy_name: Dehdadi\n"
    "type: city\n"
    "---\n\nProse that must never change.\n"
)


def _fm_lines(text):
    return text.split("---\n")[1].splitlines()


@pytest.mark.parametrize("value", [30, -45.5, 0, 0.0, 0.0001, 36000, -36000, None])
def test_server_accepts_a_sane_town_rotation(value):
    assert devserver._advanced_field_error(PAGE, {"town_rotation": value}) is None


@pytest.mark.parametrize("value", [
    "30", "abc", "", True, False, float("nan"), float("inf"), float("-inf"),
    1e-7, 0.00001, 36001, 1e9, [30], {"a": 1},
])
def test_server_refuses_anything_else(value):
    assert devserver._advanced_field_error(PAGE, {"town_rotation": value})


def test_server_still_refuses_town_rotation_when_the_file_holds_a_list():
    page = PAGE.replace("type: city\n", "type: city\ntown_rotation:\n  - 1\n  - 2\n")
    assert devserver._advanced_field_error(page, {"town_rotation": 30})


def test_town_rotation_is_a_core_field_so_advanced_does_not_list_it_twice():
    page = PAGE.replace("type: city\n", "type: city\ntown_rotation: 30\n")
    listing = devserver._frontmatter_listing(page)
    assert "town_rotation" not in listing["scalars"] and "town_rotation" not in listing["readonly"]


@pytest.mark.parametrize("value,line", [(30, "town_rotation: 30"), (-45.5, "town_rotation: -45.5"),
                                         (0, "town_rotation: 0")])
def test_save_adds_one_line_and_loses_nothing(value, line):
    after = devserver._set_frontmatter_fields(PAGE, {"town_rotation": value})
    before_lines, after_lines = _fm_lines(PAGE), _fm_lines(after)
    lost = [ln for ln in before_lines if ln not in after_lines]
    assert lost == ["last_updated: 2026-10-26"]  # bumped, not removed
    added = [ln for ln in after_lines if ln not in before_lines and not ln.startswith("last_updated:")]
    assert added == [line]
    assert after.endswith("---\n\nProse that must never change.\n")
    parsed = devserver._load_frontmatter(after)
    assert parsed["town_rotation"] == value and not isinstance(parsed["town_rotation"], str)


def test_save_replaces_in_place_and_null_removes_the_key():
    with_key = devserver._set_frontmatter_fields(PAGE, {"town_rotation": 30})
    changed = devserver._set_frontmatter_fields(with_key, {"town_rotation": 75.25})
    assert changed.count("town_rotation:") == 1 and "town_rotation: 75.25" in changed
    gone = devserver._set_frontmatter_fields(changed, {"town_rotation": None})
    assert "town_rotation" not in gone
    assert [ln for ln in _fm_lines(gone) if not ln.startswith("last_updated:")] \
        == [ln for ln in _fm_lines(PAGE) if not ln.startswith("last_updated:")]


def test_a_saved_value_is_read_back_by_the_parser(tmp_path):
    p = tmp_path / "dehdadi.md"
    p.write_text(devserver._set_frontmatter_fields(PAGE.replace("---\n\nProse", "content_type: location\n---\n\nProse"),
                                                   {"town_rotation": 12.5}), encoding="utf-8")
    assert location_parser.parse_location(p)["town_rotation"] == 12.5


# --- what the Workshop page carries ------------------------------------------

def _workshop_html(tmp_path, rotation=30.0):
    (tmp_path / "Dehdadi.geojson").write_text(json.dumps(TOWN), encoding="utf-8")
    towns = so.build_overlays([_page("dehdadi", "gm_secrets", rotation)], tmp_path)
    return gmw._build_html(EMPTY, EMPTY, EMPTY, [], [], "", "k",
                           settlements_geojson=so.feature_collection(towns),
                           town_index=so.town_index(towns)), towns


def test_the_workshop_page_carries_the_index_and_the_field(tmp_path):
    html, towns = _workshop_html(tmp_path)
    idx = so.town_index(towns)
    assert (f"var _townIdx = {json.dumps(idx, separators=(',', ':'))};" in html) is True
    for needle in ('id="ef-rot"', 'id="ef-rot-range"', "function _townGJ", "function _townAngle"):
        assert (needle in html) is True, needle


def test_the_index_is_defined_before_the_code_that_reads_it(tmp_path):
    html, _ = _workshop_html(tmp_path)
    assert html.index("var _townIdx = ") < html.index("_townIdx.forEach")


def test_a_build_with_no_index_still_works_and_carries_an_empty_one():
    html = gmw._build_html(EMPTY, EMPTY, EMPTY, [], [], "", "k")
    assert ("var _townIdx = [];" in html) is True
