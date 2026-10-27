"""
Tests for the coordinate audit (#314): utilities/locations/coord_audit.py.

Tiles and Wikidata are faked, so nothing here touches the network. Elevation tiles
are generated with Pillow as flat terrarium PNGs, one elevation per tile.
"""

import io
import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

from locations import coord_audit as ca  # noqa: E402

SOURCE = Path(ca.__file__)

pytest.importorskip("PIL")


# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------

def png_for(elev: float) -> bytes:
    from PIL import Image

    v = elev + 32768.0
    r, g, b = int(v // 256), int(v) % 256, int((v - int(v)) * 256)
    buf = io.BytesIO()
    Image.new("RGB", (256, 256), (r, g, b)).save(buf, format="PNG")
    return buf.getvalue()


def tile_of(lat: float, lon: float, z: int) -> tuple[int, int, int]:
    px, py = ca.pixel_xy(lat, lon, z)
    return z, int(px) // 256, int(py) // 256


class FakeTiles:
    """fetch(url) callable: serves a flat tile per (z, x, y), a default elsewhere."""

    def __init__(self, by_tile: dict, default: float = 1500.0, missing=()):
        self.by_tile, self.default, self.missing = by_tile, default, set(missing)
        self.calls = []

    def __call__(self, url: str):
        z, x, y = map(int, re.search(r"/(\d+)/(\d+)/(\d+)\.png$", url).groups())
        self.calls.append((z, x, y))
        if (z, x, y) in self.missing:
            return None
        return png_for(self.by_tile.get((z, x, y), self.default))


class FakeWikidata:
    """get_json(params) callable over a small table of places."""

    def __init__(self, places: dict):
        # name -> list of (qid, label, description, lat, lon)
        self.places = places
        self.calls = []

    def __call__(self, params: dict) -> dict:
        self.calls.append(params["action"])
        if params["action"] == "wbsearchentities":
            hits = self.places.get(params["search"], [])
            return {"search": [{"id": q, "label": lab, "description": d}
                               for q, lab, d, _, _ in hits]}
        found = {}
        for hits in self.places.values():
            for q, lab, d, lat, lon in hits:
                found[q] = {
                    "labels": {"en": {"value": lab}},
                    "descriptions": {"en": {"value": d}},
                    "claims": {"P625": [{"mainsnak": {"datavalue": {"value": {
                        "latitude": lat, "longitude": lon}}}}],
                              "P31": [{"mainsnak": {"datavalue": {"value": {"id": "Q486972"}}}}]},
                }
        return {"entities": {q: found[q] for q in params["ids"].split("|") if q in found}}


def make_deps(tmp_path, by_tile=None, places=None, **tile_kw):
    tiles = FakeTiles(by_tile or {}, **tile_kw)
    wd = FakeWikidata(places or {})
    cache = tmp_path / "cache"
    return (ca.TileStore(cache, fetch=tiles, sleep=lambda s: None),
            ca.Wikidata(cache, get_json=wd, sleep=lambda s: None), tiles, wd)


LOC = """---
title: {title}
content_type: location
status: {status}
visibility: gm_secrets
last_updated: 2026-05-01
{extra}location:
- {lat}
- {lon}
---
Body of {title}.
"""


def write_loc(directory: Path, slug: str, lat, lon, *, status="draft", elevation=None,
              real="", extra=""):
    lines = ""
    if elevation is not None:
        lines += f"elevation: {elevation}\n"
    if real:
        lines += f"real_world_name: {real}\n"
    lines += extra
    p = directory / f"{slug}.md"
    p.write_text(LOC.format(title=slug.title(), status=status, extra=lines, lat=lat, lon=lon),
                 encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# elevation tiles
# ---------------------------------------------------------------------------

def test_pixel_xy_origin_and_decode():
    assert ca.pixel_xy(0.0, 0.0, 0) == (128.0, 128.0)
    assert ca.decode_terrarium(128, 0, 0) == 0.0
    assert ca.decode_terrarium(131, 232, 0) == 1000.0
    assert ca.decode_terrarium(127, 255, 128) == pytest.approx(-0.5)


def test_tile_store_decodes_caches_and_counts(tmp_path):
    lat, lon = 36.21, 88.74
    fake = FakeTiles({tile_of(lat, lon, 10): 4321.0})
    store = ca.TileStore(tmp_path, fetch=fake, sleep=lambda s: None)
    assert store.elevation(lat, lon, 10) == pytest.approx(4321.0, abs=1.0)
    assert store.elevation(lat, lon, 10) == pytest.approx(4321.0, abs=1.0)
    assert store.fetched == 1 and len(fake.calls) == 1

    offline = ca.TileStore(tmp_path, offline=True, fetch=lambda u: pytest.fail("fetched"))
    assert offline.elevation(lat, lon, 10) == pytest.approx(4321.0, abs=1.0)
    assert offline.cached == 1 and offline.fetched == 0


def test_tile_store_offline_uncached_and_404_read_as_no_data(tmp_path):
    lat, lon = 36.21, 88.74
    assert ca.TileStore(tmp_path / "a", offline=True).elevation(lat, lon, 10) is None
    gone = FakeTiles({}, missing={tile_of(lat, lon, 10)})
    store = ca.TileStore(tmp_path / "b", fetch=gone, sleep=lambda s: None)
    assert store.elevation(lat, lon, 10) is None
    assert store.missing == 1
    again = ca.TileStore(tmp_path / "b", offline=True)
    assert again.elevation(lat, lon, 10) is None   # a 404 stays a 404 without refetching


def test_tile_store_budget_stops_before_the_next_download(tmp_path):
    store = ca.TileStore(tmp_path, fetch=FakeTiles({}), max_fetches=2, sleep=lambda s: None)
    store.elevation(10.0, 10.0, 10)
    store.elevation(20.0, 20.0, 10)
    with pytest.raises(ca.BudgetExceeded):
        store.elevation(30.0, 30.0, 10)


def test_relief_window_crosses_a_tile_boundary(tmp_path):
    # lon 0.0 sits exactly on the x=2048 boundary at zoom 12: left tile 100 m, right 900 m
    left = (12, 2047, tile_of(10.0, 0.0, 12)[2])
    right = (12, 2048, left[2])
    store = ca.TileStore(tmp_path, fetch=FakeTiles({left: 100.0, right: 900.0}),
                         sleep=lambda s: None)
    lo, hi = store.relief(10.0, 0.0, 12)
    assert lo == pytest.approx(100.0, abs=1.0) and hi == pytest.approx(900.0, abs=1.0)


# ---------------------------------------------------------------------------
# classification and ranking
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("field, here, relief, km, there, expected", [
    # endere-like: field matches the analog's terrain, not the current position
    (1000, 5010, (4000, 5200), 600, 1050, "coord-suspect"),
    # no elevation field, but the analog is far: analog is the only evidence
    (None, 1200, None, 300, 900, "coord-suspect"),
    # analog is far, elevation fits neither position
    (1000, 5010, (4000, 5200), 600, 3000, "ambiguous"),
    # analog is far, elevation fits the current position: elevation backs the GM's placement
    (1100, 1050, (900, 1300), 200, 3000, "ambiguous"),
    # analog is far, elevation fits both: it cannot separate them
    (1000, 1050, (900, 1300), 200, 1000, "coord-suspect"),
    # analog near, field disagrees, but sits inside the local relief
    (-300, 38, (-350, 120), 2, None, "resolution-suspect"),
    # analog near, field disagrees and relief does not explain it
    (1400, 1073, (1000, 1200), 3, None, "elevation-suspect"),
    # no analog at all, field disagrees: DEM-only, manual review
    (1400, 1073, (1000, 1200), None, None, "ambiguous"),
    # consistent: nothing to list
    (1000, 1100, None, 5, None, None),
    (None, 1100, None, None, None, None),
    (1000, 1100, None, None, None, None),
    (None, 1100, None, 5, 1000, None),
])
def test_classify(field, here, relief, km, there, expected):
    assert ca.classify(field, here, relief, km, there) == expected


def test_score_ranks_distance_and_dampens_weak_classes():
    strong = ca.score("coord-suspect", 1000, 5010, 600, analog_only=False)
    weak_only = ca.score("coord-suspect", None, 1200, 600, analog_only=True)
    resolution = ca.score("resolution-suspect", -300, 38, 2, analog_only=False)
    assert strong > weak_only
    assert strong > resolution
    # a resolution-suspect row with a 338 m gap is damped below one threshold
    assert resolution < 1.0


class StubTiles:
    def __init__(self, here, analog=None, relief=None):
        self.here, self.analog, self.rel = here, analog or {}, relief or {}

    def elevation(self, lat, lon, z):
        return self.analog.get((lat, lon), self.here.get((lat, lon)))

    def relief(self, lat, lon, z, radius_km=1.0):
        return self.rel.get((lat, lon))


class StubWikidata:
    def __init__(self, analogs):
        self.analogs = analogs
        self.prefetched = None

    def prefetch(self, names, qids):
        self.prefetched = (names, qids)

    def analog(self, name, qid=None):
        return self.analogs.get(name)


def loc_row(slug, lat, lon, elev, real="Somewhere", **kw):
    return {"slug": slug, "path": Path(f"{slug}.md"), "name": slug, "status": "draft",
            "lat": lat, "lon": lon, "elev": elev, "real_world_name": real, "wikidata": "",
            "reviewed": False, **kw}


def an(label, lat, lon):
    return {"qid": "Q1", "label": label, "description": "city", "lat": lat, "lon": lon,
            "ambiguous": False, "exact": False}


def test_build_rows_ranks_by_evidence_and_omits_consistent_and_reviewed():
    locs = [
        loc_row("far", 36.0, 88.0, 1000, real="FarPlace"),
        loc_row("mid", 40.0, 70.0, 1000, real="MidPlace"),
        loc_row("small", 41.0, 71.0, -300, real="SmallPlace"),
        loc_row("fine", 42.0, 72.0, 1000, real="FinePlace"),
        loc_row("done", 43.0, 73.0, 1000, real="DonePlace", reviewed=True),
    ]
    tiles = StubTiles(
        here={(36.0, 88.0): 5010, (40.0, 70.0): 1050, (41.0, 71.0): 38, (42.0, 72.0): 1020,
              (43.0, 73.0): 5000},
        analog={(37.0, 94.0): 1050, (40.5, 72.0): 1000},
        relief={(41.0, 71.0): (-350.0, 120.0), (36.0, 88.0): (4000.0, 5200.0)})
    wd = StubWikidata({"FarPlace": an("Far", 37.0, 94.0), "MidPlace": an("Mid", 40.5, 72.0),
                       "SmallPlace": an("Small", 41.0, 71.01), "FinePlace": None})
    rows, counts = ca.build_rows(locs, tiles, wd)
    assert [r["slug"] for r in rows] == ["far", "mid", "small"]
    assert [r["rank"] for r in rows] == [1, 2, 3]
    assert rows[0]["class"] == "coord-suspect"
    assert rows[0]["suggest_lat"] == "37.0000" and rows[0]["suggest_lon"] == "94.0000"
    assert rows[2]["class"] == "resolution-suspect" and rows[2]["suggest_elev"] == ""
    assert counts == {"checked": 4, "consistent": 1, "reviewed": 1}
    assert wd.prefetched[0] == ["FarPlace", "MidPlace", "SmallPlace", "FinePlace"]


def test_field_contradicting_terrain_outranks_a_distant_name_match():
    """A generic name matching a place 3000 km away must not outrank a 4000 m elevation miss."""
    locs = [
        loc_row("generic", 40.0, 70.0, None, real="Yuli"),
        loc_row("endere", 36.0, 88.0, 1000, real=""),
        loc_row("modest", 41.0, 71.0, 1000, real=""),
    ]
    tiles = StubTiles(
        here={(40.0, 70.0): 890, (36.0, 88.0): 5008, (41.0, 71.0): 1400},
        analog={(23.0, 121.0): 575},
        relief={(36.0, 88.0): (4900.0, 5100.0), (41.0, 71.0): (1380.0, 1420.0)})
    wd = StubWikidata({"Yuli": an("Yuli Township", 23.0, 121.0)})
    rows, _ = ca.build_rows(locs, tiles, wd)
    by_slug = {r["slug"]: r for r in rows}
    assert by_slug["generic"]["_score"] > by_slug["endere"]["_score"]   # distance alone would win
    assert [r["slug"] for r in rows] == ["endere", "modest", "generic"]


def test_build_rows_end_to_end_with_fake_tiles_and_wikidata(tmp_path):
    d = tmp_path / "locations"
    d.mkdir()
    write_loc(d, "endere", 36.21, 88.74, elevation=1000, real="Niya", status="canon")
    write_loc(d, "calm", 38.0, 80.0, elevation=1500, real="Calmtown")
    write_loc(d, "zzstub", 1, 1)           # skipped like the generators
    (d / "_TEMPLATE_location.md").write_text("---\ntitle: t\n---\n", encoding="utf-8")
    nocoord = d / "nocoord.md"
    nocoord.write_text("---\ntitle: N\ncontent_type: location\nstatus: draft\n---\nx\n",
                       encoding="utf-8")
    locs, no_coords = ca.load_locations(d)
    assert sorted(l["slug"] for l in locs) == ["calm", "endere"] and no_coords == 1

    niya = (37.0, 82.0)
    by_tile = {tile_of(36.21, 88.74, 10): 5010.0, tile_of(36.21, 88.74, 12): 5010.0,
               tile_of(*niya, 10): 1050.0}
    store, wd, _, wd_fake = make_deps(
        tmp_path, by_tile, {"Niya": [("Q10", "Niya", "ancient city", *niya)],
                            "Calmtown": [("Q11", "Calmtown", "town", 38.0, 80.0)]})
    rows, counts = ca.build_rows(locs, store, wd)
    assert [r["slug"] for r in rows] == ["endere"]
    row = rows[0]
    assert row["class"] == "coord-suspect" and row["lock"] == "🔒"
    assert row["wikidata"] == "Q10" and row["dem_here"] == "5010" and row["dem_analog"] == "1050"
    assert float(row["km"]) > 400
    assert counts["consistent"] == 1

    # a second run reuses every cached tile and Wikidata answer
    store2 = ca.TileStore(tmp_path / "cache", offline=True)
    wd2 = ca.Wikidata(tmp_path / "cache", offline=True)
    again, _ = ca.build_rows(locs, store2, wd2)
    assert [r["slug"] for r in again] == ["endere"]


def test_report_files_share_rows_and_are_never_overwritten(tmp_path):
    rows = [{**{c: "" for c in ca.COLUMNS}, "rank": 1, "slug": "a|b", "note": "x | y",
             "_score": 2.0}]
    import datetime
    now = datetime.datetime(2026, 10, 26, 12, 0, 0)
    md1, csv1 = ca.write_report(rows, tmp_path / "out", now)
    md2, csv2 = ca.write_report(rows, tmp_path / "out", now)
    assert md1 != md2 and csv1 != csv2 and md1.exists() and md2.exists()
    assert "a\\|b" in md1.read_text(encoding="utf-8")
    assert ca.read_decisions(csv1)[0]["slug"] == "a|b"
    assert ca.read_decisions(md1)[0]["slug"] == "a|b"
    assert ca.read_decisions(md1)[0]["note"] == "x | y"


# ---------------------------------------------------------------------------
# Wikidata
# ---------------------------------------------------------------------------

def test_wikidata_first_in_region_hit_and_ambiguity(tmp_path):
    places = {"Springfield": [("Q1", "Springfield", "US city", 39.8, -89.6),       # outside the map
                              ("Q2", "Springfield", "town", 40.0, 70.0),
                              ("Q3", "Springfield", "village", 45.0, 100.0)]}
    wd = ca.Wikidata(tmp_path, get_json=FakeWikidata(places), sleep=lambda s: None)
    wd.prefetch(["Springfield"], [])
    a = wd.analog("Springfield")
    assert a["qid"] == "Q2" and a["ambiguous"] is True        # Q3 is > 100 km from Q2

    solo = {"Kashgar": [("Q4", "Kashgar", "city", 39.47, 75.99)]}
    wd2 = ca.Wikidata(tmp_path / "solo", get_json=FakeWikidata(solo), sleep=lambda s: None)
    wd2.prefetch(["Kashgar"], [])
    assert wd2.analog("Kashgar")["ambiguous"] is False


def test_wikidata_exact_id_skips_the_search_and_missing_name_has_no_analog(tmp_path):
    fake = FakeWikidata({"Whatever": [("Q9", "Nine", "city", 40.0, 80.0)]})
    wd = ca.Wikidata(tmp_path, get_json=fake, sleep=lambda s: None)
    wd.prefetch([], ["Q9"])
    assert "wbsearchentities" not in fake.calls
    got = wd.analog("anything", "Q9")
    assert got["qid"] == "Q9" and got["exact"] is True
    assert wd.analog("", None) is None and wd.analog(None, None) is None


def test_wikidata_batches_entities_and_caches(tmp_path):
    places = {f"P{i}": [(f"Q{100 + i}", f"P{i}", "town", 30.0 + i * 0.1, 80.0)] for i in range(60)}
    fake = FakeWikidata(places)
    wd = ca.Wikidata(tmp_path, get_json=fake, sleep=lambda s: None)
    wd.prefetch(list(places), [])
    assert fake.calls.count("wbsearchentities") == 60
    assert fake.calls.count("wbgetentities") == 2            # 60 ids -> 50 + 10
    before = len(fake.calls)
    wd.prefetch(list(places), [])
    assert len(fake.calls) == before                         # all cached


def test_requests_are_polite_and_never_use_maptiler():
    src = SOURCE.read_text(encoding="utf-8")
    assert "api.maptiler.com" not in src
    assert "github.com/mofro/tarim-shaiel-campaign-frame" in ca.USER_AGENT
    assert "@" not in ca.USER_AGENT
    assert ca.TILE_URL.startswith("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/")


# ---------------------------------------------------------------------------
# applying decisions
# ---------------------------------------------------------------------------

def decision_row(slug, decision, **kw):
    base = {c: "" for c in ca.COLUMNS}
    base.update({"slug": slug, "decision": decision}, **kw)
    return base


def write_decisions_csv(path: Path, rows: list[dict]) -> Path:
    path.write_text(ca.render_csv(rows), encoding="utf-8")
    return path


@pytest.fixture
def vault(tmp_path):
    d = tmp_path / "world" / "locations"
    d.mkdir(parents=True)
    write_loc(d, "mover", 36.21, 88.74, elevation=1000, real="Niya")
    write_loc(d, "lifter", 40.0, 70.0, elevation=1400)
    write_loc(d, "keeper", 41.0, 71.0, elevation=-154)
    write_loc(d, "idle", 42.0, 72.0, elevation=500)
    write_loc(d, "canonical", 43.0, 73.0, elevation=900, status="canon")
    routes = tmp_path / "world" / "data" / "routes.geojson"
    routes.parent.mkdir(parents=True)
    routes.write_text(json.dumps({"type": "FeatureCollection", "features": [
        {"type": "Feature", "id": "route_a", "properties": {},
         "geometry": {"type": "LineString", "coordinates": [[88.74, 36.21], [90.0, 37.0]]}},
        {"type": "Feature", "id": "route_b", "properties": {},
         "geometry": {"type": "LineString", "coordinates": [[10.0, 10.0], [88.7401, 36.2101]]}},
        {"type": "Feature", "id": "route_c", "properties": {},
         "geometry": {"type": "LineString", "coordinates": [[10.0, 10.0], [11.0, 11.0]]}},
    ]}), encoding="utf-8")
    return d, routes


def snapshot(d: Path) -> dict:
    return {p.name: p.read_bytes() for p in d.glob("*.md")}


def changed_lines(before: str, after: str) -> set[str]:
    b, a = before.splitlines(), after.splitlines()
    return {l for l in a if l not in b} | {("-" + l) for l in b if l not in a}


def test_move_changes_only_location_and_last_updated(vault, tmp_path):
    d, routes = vault
    before = snapshot(d)
    f = write_decisions_csv(tmp_path / "a.csv", [decision_row(
        "mover", "move", lat="36.21", lon="88.74", elev_field="1000", wikidata="Q10", km="500",
        suggest_lat="37.0000", suggest_lon="82.0000")])
    out = []
    assert ca.apply_decisions(f, d, routes, dry_run=False, confirm_canon=False, out=out.append) == 0
    after = snapshot(d)
    assert [n for n in after if after[n] != before[n]] == ["mover.md"]
    text = after["mover.md"].decode()
    assert "- 37.0" in text and "- 82.0" in text and "wikidata: Q10" in text
    assert "elevation: 1000" in text
    today = ca.datetime.date.today().isoformat()
    assert f"last_updated: {today}" in text
    assert "coord_review" not in text
    joined = "\n".join(out)
    assert "route_a" in joined and "route_b" in joined and "route_c" not in joined


def test_elevation_changes_only_elevation(vault, tmp_path):
    d, routes = vault
    before = snapshot(d)
    f = write_decisions_csv(tmp_path / "a.csv", [decision_row(
        "lifter", "elevation", lat="40", lon="70", elev_field="1400", suggest_elev="1073",
        wikidata="Q5", km="3")])
    assert ca.apply_decisions(f, d, routes, dry_run=False, confirm_canon=False, out=lambda s: None) == 0
    text = (d / "lifter.md").read_text(encoding="utf-8")
    assert "elevation: 1073" in text and "wikidata: Q5" in text
    assert "- 40.0" in text or "- 40\n" in text      # coordinates untouched
    after = snapshot(d)
    assert [n for n in after if after[n] != before[n]] == ["lifter.md"]


def test_elevation_does_not_confirm_a_far_analog(vault, tmp_path):
    d, routes = vault
    f = write_decisions_csv(tmp_path / "a.csv", [decision_row(
        "lifter", "elevation", lat="40", lon="70", elev_field="1400", suggest_elev="1073",
        wikidata="Q5", km="400")])
    ca.apply_decisions(f, d, routes, dry_run=False, confirm_canon=False, out=lambda s: None)
    assert "wikidata" not in (d / "lifter.md").read_text(encoding="utf-8")


def test_intentional_stamps_review_and_drops_the_row_next_time(vault, tmp_path):
    d, routes = vault
    f = write_decisions_csv(tmp_path / "a.csv", [decision_row(
        "keeper", "intentional", lat="41", lon="71", elev_field="-154", wikidata="Q7")])
    assert ca.apply_decisions(f, d, routes, dry_run=False, confirm_canon=False, out=lambda s: None) == 0
    text = (d / "keeper.md").read_text(encoding="utf-8")
    assert "coord_review: intentional" in text
    assert f"coord_reviewed: {ca.datetime.date.today().isoformat()}" in text
    assert "wikidata" not in text
    locs, _ = ca.load_locations(d)
    keeper = next(l for l in locs if l["slug"] == "keeper")
    assert keeper["reviewed"] is True
    rows, counts = ca.build_rows(locs, StubTiles(here={}), StubWikidata({}))
    assert "keeper" not in [r["slug"] for r in rows] and counts["reviewed"] == 1


def test_skip_and_blank_write_nothing(vault, tmp_path):
    d, routes = vault
    before = snapshot(d)
    f = write_decisions_csv(tmp_path / "a.csv", [
        decision_row("mover", "", lat="36.21", lon="88.74", elev_field="1000"),
        decision_row("lifter", "skip", lat="40", lon="70", elev_field="1400"),
        decision_row("idle", "  SKIP ", lat="42", lon="72", elev_field="500")])
    out = []
    assert ca.apply_decisions(f, d, routes, dry_run=False, confirm_canon=False, out=out.append) == 0
    assert snapshot(d) == before
    assert "0 file(s)" in out[-1] and "3 row(s) skipped" in out[-1]


def test_dry_run_prints_the_diff_and_writes_nothing(vault, tmp_path):
    d, routes = vault
    before = snapshot(d)
    f = write_decisions_csv(tmp_path / "a.csv", [decision_row(
        "lifter", "elevation", lat="40", lon="70", elev_field="1400", suggest_elev="1073")])
    out = []
    assert ca.apply_decisions(f, d, routes, dry_run=True, confirm_canon=False, out=out.append) == 0
    assert snapshot(d) == before
    printed = "\n".join(out)
    assert "-elevation: 1400" in printed and "+elevation: 1073" in printed
    assert "would change 1 file(s)" in printed


def test_canon_needs_the_extra_confirmation(vault, tmp_path):
    d, routes = vault
    before = snapshot(d)
    row = decision_row("canonical", "elevation", lat="43", lon="73", elev_field="900",
                       suggest_elev="800")
    f = write_decisions_csv(tmp_path / "a.csv", [row])
    out = []
    assert ca.apply_decisions(f, d, routes, dry_run=False, confirm_canon=False, out=out.append) == 2
    assert snapshot(d) == before and "--confirm-canon" in "\n".join(out)
    assert ca.apply_decisions(f, d, routes, dry_run=False, confirm_canon=True, out=lambda s: None) == 0
    assert "elevation: 800" in (d / "canonical.md").read_text(encoding="utf-8")


def test_one_bad_row_blocks_every_write(vault, tmp_path):
    d, routes = vault
    before = snapshot(d)
    f = write_decisions_csv(tmp_path / "a.csv", [
        decision_row("lifter", "elevation", lat="40", lon="70", elev_field="1400",
                     suggest_elev="1073"),
        decision_row("idle", "mvoe", lat="42", lon="72", elev_field="500"),
        decision_row("keeper", "elevation", lat="41", lon="71", elev_field="-154",
                     suggest_elev="")])
    out = []
    assert ca.apply_decisions(f, d, routes, dry_run=False, confirm_canon=False, out=out.append) == 2
    assert snapshot(d) == before
    printed = "\n".join(out)
    assert "mvoe" in printed and "suggest_elev" in printed


def test_stale_row_is_refused(vault, tmp_path):
    d, routes = vault
    before = snapshot(d)
    f = write_decisions_csv(tmp_path / "a.csv", [
        decision_row("lifter", "elevation", lat="40", lon="70", elev_field="1111",
                     suggest_elev="1073"),
        decision_row("idle", "move", lat="45", lon="72", elev_field="500",
                     suggest_lat="1", suggest_lon="2")])
    out = []
    assert ca.apply_decisions(f, d, routes, dry_run=False, confirm_canon=False, out=out.append) == 2
    assert snapshot(d) == before
    assert out.count("  - lifter: stale row — the file's elevation changed since the report was "
                     "made; re-run the audit") == 1
    assert any("idle: stale row" in line for line in out)


def test_markdown_decision_file_round_trips(vault, tmp_path):
    d, routes = vault
    rows = [decision_row("lifter", "elevation", lat="40", lon="70", elev_field="1400",
                         suggest_elev="1073", note="has | a pipe")]
    md = tmp_path / "a.md"
    md.write_text(ca.render_markdown(rows, "stamp"), encoding="utf-8")
    parsed = ca.read_decisions(md)
    assert parsed[0]["decision"] == "elevation" and parsed[0]["note"] == "has | a pipe"
    assert ca.apply_decisions(md, d, routes, dry_run=False, confirm_canon=False,
                              out=lambda s: None) == 0
    assert "elevation: 1073" in (d / "lifter.md").read_text(encoding="utf-8")


def test_decision_file_without_a_table_is_an_error(tmp_path):
    f = tmp_path / "empty.md"
    f.write_text("# nothing here\n", encoding="utf-8")
    with pytest.raises(ca.AuditError):
        ca.read_decisions(f)


def test_routes_touching_matches_either_end_within_a_kilometre(vault):
    _, routes = vault
    assert ca.routes_touching(routes, 36.21, 88.74) == ["route_a", "route_b"]
    assert ca.routes_touching(routes, 0.0, 0.0) == []
    assert ca.routes_touching(routes.parent / "missing.geojson", 1, 1) == []
