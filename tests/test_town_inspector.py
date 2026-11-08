"""
GM-only town inspector (#399): the data module, the two devserver routes, and the rule that
nothing is written where a player build could pick it up.
"""

import http.server
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities"))
sys.path.insert(0, str(ROOT / "utilities" / "geojson"))
sys.path.insert(0, str(Path(__file__).parent))

import devserver
import settlement_profiles as sp
from geojson import town_inspector as ti
from test_settlement_profiles import FACTION_BLOCK, _with_factions, vault  # noqa: F401


@pytest.fixture
def drafted(vault):  # noqa: F811
    _with_factions(vault, FACTION_BLOCK)
    sp.draft("Testburg", vault)
    return vault


# -- S1: the payload ties buildings, people and factions together ---------------------------

def test_s1_payload_counts_and_links(drafted):
    p = ti.payload("Testburg", drafted)
    gm = json.loads((sp.derived_dir(drafted) / "Testburg.gm.json").read_text())
    assert len(p["buildings"]) == len(gm["buildings"]) == 9
    assert len(p["people"]) == len(gm["people"]) == 8
    for pid, person in p["people"].items():
        if person["work"] is not None:
            assert pid in p["buildings"][person["work"]]["works"]
        if person["home"] is not None:
            assert pid in p["buildings"][person["home"]]["lives"]


def test_s1_seat_and_membership_come_from_the_sidecar(drafted):
    p = ti.payload("Testburg", drafted)
    assert p["buildings"][10]["seats"] == ["watch-order"]
    assert any("secret-cell" in f for f in p["people"][106]["factions"])


def test_s1_ftg_originals_shown_while_the_export_exists_and_not_after(drafted):
    p = ti.payload("Testburg", drafted)
    assert p["buildings"][10]["ftg"]["name"] == "Big Inn"
    assert p["people"][100]["ftg"]["name"] == "F100 Ryke"
    assert p["locked_source"] is False
    (sp.cities_dir(drafted) / "Testburg.json").unlink()
    q = ti.payload("Testburg", drafted)
    assert q["locked_source"] is True
    assert q["buildings"][10]["ftg"] is None and q["people"][100]["ftg"] is None


def test_s1_geometry_is_the_derived_geojson(drafted):
    p = ti.payload("Testburg", drafted)
    derived = json.loads((sp.derived_dir(drafted) / "Testburg.geojson").read_text())
    assert p["geojson"] == derived


# -- S2: bad names and missing drafts -------------------------------------------------------

@pytest.mark.parametrize("name", ["", "../etc", "..", "a/b", "a\\b", ".hidden", "x" * 80,
                                  "Test burg", "%2e%2e", "Testburg\n"])
def test_s2_malformed_names_are_refused(drafted, name):
    with pytest.raises(ti.NoSuchTown):
        ti.load(name, drafted)


def test_s2_a_town_without_a_draft_is_refused(vault):  # noqa: F811
    with pytest.raises(ti.NoSuchTown):
        ti.load("Testburg", vault)


# -- S3: the routes -------------------------------------------------------------------------

@pytest.fixture
def served(drafted, monkeypatch):
    monkeypatch.setattr(sp, "VAULT_ROOT", drafted)
    real_load, real_payload = ti.load, ti.payload
    monkeypatch.setattr(ti, "load", lambda t, root=drafted: real_load(t, root))
    monkeypatch.setattr(ti, "payload", lambda t, root=drafted: real_payload(t, root))
    real_at = ti.at
    monkeypatch.setattr(ti, "at", lambda t, d, h, root=drafted: real_at(t, d, h, root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), devserver._Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


class _Remote(devserver._Handler):
    @property
    def client_address(self):
        return ("192.168.1.50", 40000)

    @client_address.setter
    def client_address(self, value):
        pass


@pytest.fixture
def served_remote(drafted, monkeypatch):
    real_load = ti.load
    monkeypatch.setattr(ti, "load", lambda t, root=drafted: real_load(t, root))
    real_at = ti.at
    monkeypatch.setattr(ti, "at", lambda t, d, h, root=drafted: real_at(t, d, h, root))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Remote)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join(timeout=5)


def _get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, b""


def test_s3_api_returns_the_payload_with_no_cors_header(served):
    status, headers, body = _get(served + "/api/town/Testburg")
    assert status == 200
    assert json.loads(body)["town"] == "Testburg"
    assert headers.get("Access-Control-Allow-Origin") is None
    assert headers["Cache-Control"] == "no-store"


def test_s3_page_is_served_as_html(served):
    status, headers, body = _get(served + "/town/Testburg")
    assert status == 200
    assert headers["Content-Type"].startswith("text/html")
    assert b"Town Inspector" in body


@pytest.mark.parametrize("route", ["/town/Nowhere", "/api/town/Nowhere", "/town/..%2f..%2fREADME",
                                   "/api/town/%2e%2e"])
def test_s3_unknown_or_hostile_names_are_404(served, route):
    assert _get(served + route)[0] == 404


@pytest.mark.parametrize("route", ["/town/Testburg", "/api/town/Testburg"])
def test_s3_non_local_clients_are_refused(served_remote, route):
    assert _get(served_remote + route)[0] == 403


# -- S4: nothing lands where a player build could publish it --------------------------------

def test_s4_serving_writes_nothing_and_docs_gets_no_town_data(drafted, served):
    before = sorted(p.relative_to(drafted) for p in drafted.rglob("*"))
    _get(served + "/town/Testburg")
    _get(served + "/api/town/Testburg")
    assert sorted(p.relative_to(drafted) for p in drafted.rglob("*")) == before
    assert not (drafted / "docs").exists()


def test_s4_the_page_never_names_gm_data_in_itself():
    page = ti.PAGE_PATH.read_text(encoding="utf-8")
    assert "Chain-Breakers" not in page and "secret-cell" not in page


# -- S6: time of day (derived placement) ----------------------------------------------------

import town_schedule as ts  # noqa: E402

BLDGS = {
    1: {"id": 1, "specificBuildingType": "middle class home"},
    2: {"id": 2, "specificBuildingType": "tanner",
        "openingTimes": {"openHour": 9, "closeHour": 17, "closedDays": [6, 7]}},
    3: {"id": 3, "specificBuildingType": "tavern", "openingTimes": {"openHour": 11, "closeHour": 1, "closedDays": []}},
    4: {"id": 4, "specificBuildingType": "school"},
}


def _p(**kw):
    return {"id": 1, "placeOfResidence": 1, **kw}


def test_s6_spans_wrap_past_midnight():
    assert ts.in_span(23, 22, 6) and ts.in_span(3, 22, 6) and not ts.in_span(12, 22, 6)
    assert ts.in_span(10, 9, 17) and not ts.in_span(17, 9, 17)


def test_s6_worker_follows_building_hours_and_rests_on_closed_days():
    p = _p(placeOfWork=2)
    assert ts.where(p, BLDGS, [], 2, 10) == (2, "working")
    assert ts.where(p, BLDGS, [], 2, 3) == (1, "asleep")
    assert ts.where(p, BLDGS, [], 6, 10)[0] == 1  # Saturday: closed


def test_s6_night_shift_belongs_to_the_day_it_started():
    p = _p(placeOfWork=3)
    assert ts.where(p, BLDGS, [], 5, 23) == (3, "working")
    assert ts.where(p, BLDGS, [], 6, 0) == (3, "working")


def test_s6_students_attend_on_weekdays_only():
    p = _p(placeOfStudy=4)
    assert ts.where(p, BLDGS, [], 3, 10) == (4, "studying")
    assert ts.where(p, BLDGS, [], 6, 10)[0] == 1


def test_s6_snapshot_is_deterministic_and_counts_match():
    people = [_p(id=i, placeOfWork=2 if i % 2 else None) for i in range(1, 21)]
    a = ts.snapshot(people, BLDGS, 3, 10)
    assert a == ts.snapshot(people, BLDGS, 3, 10)
    assert sum(a["count"].values()) == sum(1 for v in a["where"].values() if v[0] is not None)
    assert a["count"][2] == 10


def test_s6_at_covers_everyone_and_rejects_bad_times(drafted):
    s = ti.at("Testburg", 3, 10, drafted)
    assert len(s["where"]) == 8
    for bad in [(0, 5), (8, 5), (1, -1), (1, 24)]:
        with pytest.raises(ValueError):
            ti.at("Testburg", *bad, drafted)


def test_s6_route_returns_snapshot_and_refuses_bad_or_remote(served, served_remote):
    status, headers, body = _get(served + "/api/town/Testburg/at?day=3&hour=10")
    assert status == 200 and headers["Cache-Control"] == "no-store"
    assert headers.get("Access-Control-Allow-Origin") is None
    assert json.loads(body)["hour"] == 10
    assert _get(served + "/api/town/Testburg/at?day=9&hour=10")[0] == 400
    assert _get(served + "/api/town/Testburg/at")[0] == 400
    assert _get(served + "/api/town/Nowhere/at?day=1&hour=1")[0] == 404
    assert _get(served_remote + "/api/town/Testburg/at?day=3&hour=10")[0] == 403


# -- S7: the roster (filters over the payload the page already has) ---------------------------

def test_s7_page_has_roster_and_every_filter_field_exists_on_people(drafted):
    page = ti.PAGE_PATH.read_text(encoding="utf-8")
    assert 'id="roster-btn"' in page and "rosterMatches" in page
    person = next(iter(ti.payload("Testburg", drafted)["people"].values()))
    # the roster filters read these keys; the page breaks silently if one is renamed
    assert set(person) >= {"name", "race", "religion", "job", "factions", "work"}


# -- S5: what the panels show (#399 review) -------------------------------------------------

def test_s5_person_carries_personality_inputs_and_family(drafted):
    p = ti.payload("Testburg", drafted)
    for person in p["people"].values():
        assert set(person) >= {"core", "stats", "height", "study", "trait", "parents", "siblings", "children"}
        assert person["id"] not in person["siblings"]
        for kin in person["parents"] + person["siblings"] + person["children"]:
            assert kin in p["people"]


def test_s5_family_links_are_symmetric(drafted):
    p = ti.payload("Testburg", drafted)
    for pid, person in p["people"].items():
        for c in person["children"]:
            assert pid in p["people"][c]["parents"]
        for s in person["siblings"]:
            assert pid in p["people"][s]["siblings"]


def test_s5_buildings_carry_hours_key(drafted):
    p = ti.payload("Testburg", drafted)
    assert all("hours" in b for b in p["buildings"].values())


# -- hours (#406) -----------------------------------------------------------------------

def test_khans_and_caravanserai_are_not_free_time_venues():
    b = {1: {"specificBuildingType": "khan"}, 2: {"specificBuildingType": "caravanserai"},
         3: {"specificBuildingType": "tavern", "openingTimes": {"closedDays": [], "openHour": 15, "closeHour": 21}},
         9: {"specificBuildingType": "house"}}
    people = [{"id": i, "placeOfResidence": 9} for i in range(60)]
    snap = ts.snapshot(people, b, 2, 19)
    assert not snap["count"].get(1) and not snap["count"].get(2) and snap["count"].get(3)


def test_round_clock_inn_staff_rotate_over_the_watches_and_a_school_rests_on_its_closed_day():
    inn = {"specificBuildingType": "small inn"}
    staff = [{"id": i, "jobTitle": "Cook", "placeOfWork": 1} for i in range(30)]
    assert {ts.shift_of(p, inn) for p in staff} == set(ts.GUARD_SHIFTS)
    school = {"specificBuildingType": "school", "openingTimes": {"closedDays": [5], "openHour": 7, "closeHour": 14}}
    kid = {"id": 1, "placeOfResidence": 9, "placeOfStudy": 4}
    b = {4: school, 9: {"specificBuildingType": "house"}}
    assert ts.where(kid, b, [], 4, 10) == (4, "studying")
    assert ts.where(kid, b, [], 5, 10)[1] != "studying"


# -- evenings out (#406) ----------------------------------------------------------------

def _evening_town(n=600):
    b = {1: {"specificBuildingType": "house"}, 2: {"specificBuildingType": "house"},
         3: {"specificBuildingType": "tavern", "openingTimes": {"closedDays": [], "openHour": 15, "closeHour": 21}}}
    people = [{"id": i, "age": 30, "placeOfResidence": 1 + i % 2, "placeOfWork": 7} for i in range(n)]
    return b, people


def test_evening_splits_between_drink_friends_streets_and_home():
    b, people = _evening_town()
    why = [w[1] for w in ts.snapshot(people, b, 2, 19)["where"].values()]
    for reason in ("free time", "visiting friends", "out walking", "at home"):
        assert why.count(reason) > 30, reason


def test_children_stay_in_of_an_evening():
    b, people = _evening_town()
    for p in people:
        p["age"] = 9
    why = {w[1] for w in ts.snapshot(people, b, 2, 19)["where"].values()}
    assert why == {"at home"}


def test_a_tavern_turns_away_drinkers_past_its_evening_cap():
    b, people = _evening_town(6000)
    snap = ts.snapshot(people, b, 2, 19)
    assert snap["count"][3] <= ts.EVENING_CAP["tavern"]
    assert sum(1 for w in snap["where"].values() if w[1] == "free time") == snap["count"][3]


def test_inns_and_caravanserai_are_rated_for_the_night_and_nothing_else_is():
    b = {1: {"specificBuildingType": "caravanserai"}, 2: {"specificBuildingType": "small inn"},
         3: {"specificBuildingType": "house"}, 4: {"specificBuildingType": "tavern"}}
    rated = ts.lodging(b, 2)
    assert set(rated) == {1, 2}
    assert all(5 <= v["pct"] <= 100 and v["rating"] for v in rated.values())
    assert ts.lodging(b, 2) == rated
    assert len({ts.lodging(b, d)[1]["pct"] for d in range(1, 8)}) > 1
    assert ts.snapshot([], b, 2, 3)["lodging"] == rated


def test_every_building_type_gets_a_labelled_room_list():
    import town_rooms as tr
    assert tr.rooms(None) is None
    for t, kind in [("tavern", "drinking house"), ("upper class home", "rich home"),
                    ("barracks", "barracks"), ("temple", "temple"), ("tanner", "workshop")]:
        r = tr.rooms(t)
        assert r["kind"] == kind and len(r["rooms"]) >= 4
    assert set(tr.KIND_OF.values()) <= set(tr.KINDS)


def test_payload_carries_suggested_rooms_per_building(drafted):
    d = ti.payload("Testburg", drafted)
    assert all("suggestedRooms" in b for b in d["buildings"].values())


# -- Daggerheart Difficulty and fight stats (#409) ----------------------------------------

def _person(job="Guard", race="Human", age=30, **ab):
    keys = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
    return {"job": job, "race": race, "age": age, "stats": {k: ab.get(k, 10) for k in keys}}


def test_every_job_in_the_real_qarshi_resolves_to_a_role():
    import town_daggerheart as dh
    gm = ROOT / "world" / "maps" / "cities" / "derived" / "Qarshi.gm.json"
    if not gm.exists():
        pytest.skip("Qarshi is not drafted here")
    titles = {p.get("jobTitle") for p in json.loads(gm.read_text())["people"] if p.get("jobTitle")}
    assert [t for t in sorted(titles) if dh.job_row(t)[0] is dh.DEFAULT_JOB] == []


def test_difficulty_follows_role_tier_ability_and_life_stage():
    import town_daggerheart as dh
    guard = dh.stats(_person("Guard", strength=13))
    assert (guard["role"], guard["tier"], guard["difficulty"]) == ("Standard", 1, 12)
    assert dh.stats(_person("Guard", strength=16))["role"] == "Bruiser"
    assert dh.stats(_person("Guard", strength=3, dexterity=3))["difficulty"] == 11
    assert dh.stats(_person("Guard", age=8))["difficulty"] == 10  # a child
    assert dh.stats(_person("Guard", age=90))["stage"] == "elder"
    app = dh.stats(_person("Tanner's apprentice"))
    assert app["difficulty"] == dh.stats(_person("Tanner"))["difficulty"] - 1
    assert dh.stats(_person("Merchant", wisdom=15))["difficulty"] == 11
    assert dh.stats(_person("Merchant", race="Div-Born", age=200))["tier"] == 2


def test_minions_have_one_hp_and_no_thresholds_others_have_both():
    import town_daggerheart as dh
    m = dh.stats(_person("Labourer"))
    assert m["hp"] == 1 and m["thresholds"] is None
    s = dh.stats(_person("Guard"))
    assert s["hp"] >= 3 and s["thresholds"][0] < s["thresholds"][1]
    t2 = dh.stats(_person("Guard", race="Div-Born", age=200))
    assert t2["difficulty"] > s["difficulty"] and t2["hp"] > s["hp"]


def test_unknown_title_and_missing_stats_still_give_a_value_and_it_is_deterministic():
    import town_daggerheart as dh
    p = {"job": "Zeppelin pilot", "race": "Human", "age": None, "stats": None}
    assert dh.stats(p) == dh.stats(dict(p)) and dh.stats(p)["role"] == "Minion"


def test_payload_carries_daggerheart_for_every_person(drafted):
    d = ti.payload("Testburg", drafted)
    assert all({"role", "difficulty", "hp", "attack"} <= set(p["dh"]) for p in d["people"].values())
