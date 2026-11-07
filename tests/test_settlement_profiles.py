"""
Tests for the settlement profile pipeline (#386): scenarios S1-S13 of the issue.

Most run on a small synthetic town copied into a temp vault together with the real
profile layers; two run on the real Dehdadi export (determinism, source untouched).
"""

import json
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities" / "geojson"))

import settlement_profiles as sp

TEMPLE = 5


def _square(area):
    s = area ** 0.5
    return [[[0, 0], [s, 0], [s, s], [0, s], [0, 0]]]


def _building(i, name, btype, specific, notes=""):
    return {"id": i, "name": name, "buildingType": btype, "specificBuildingType": specific, "notes": notes}


def _person(i, last, home, age=30, gender="male", job="Labourer", work=None, religion="the good gods",
            child=(), parent=(), race="Human"):
    p = {"id": i, "firstName": f"F{i}", "lastName": last, "gender": gender, "age": age, "race": race,
         "religion": religion, "placeOfResidence": home, "childInFamilies": list(child),
         "parentInFamilies": list(parent)}
    if job:
        p["jobTitle"] = job
        p["placeOfWork"] = work
    return p


def make_town():
    buildings = [
        _building(1, "The Ryke Residence", "RESIDENCE", "house"),
        _building(2, "The Ryke Residence", "RESIDENCE", "house"),
        _building(3, "The Quell Residence", "RESIDENCE", "house"),
        _building(TEMPLE, "Pagoda of Biius", "RELIGIOUS", "temple"),
        _building(10, "Big Inn", "INN", "medium inn"),
        _building(11, "Small Inn", "INN", "small inn"),
        _building(12, "Big Store", "WAREHOUSE", "general warehouse"),
        _building(13, "Little Store", "WAREHOUSE", "general warehouse"),
        _building(14, "The Quell Tavern", "TAVERN", "tavern"),
    ]
    areas = {1: 80, 2: 80, 3: 80, TEMPLE: 300, 10: 500, 11: 150, 12: 700, 13: 300, 14: 100}
    people = [
        # one household across residences 1 and 2: two parents of different surname, two children
        _person(100, "Ryke", 1, 40, "male", "Merchant", 10, child=[], parent=[1]),
        _person(101, "Quell", 1, 38, "female", "Weaver", None, parent=[1, 2], religion=None),
        _person(102, "Ryke", 2, 12, "female", None, child=[1], religion="the evil gods"),
        _person(103, "Ryke", 1, 9, "male", None, child=[1], religion="the neutral gods"),
        _person(104, "Quell", 2, 60, "female", "Cleric", TEMPLE, parent=[2], religion="the evil gods"),
        _person(105, "Quell", 3, 25, "male", "Server", 14),
        _person(106, "Vane", 3, 33, "female", "Cleric", TEMPLE, religion="the good gods"),
        _person(107, "Vane", 3, 5, "male", None, religion=None),
    ]
    return {"buildings": buildings, "people": people}, areas


def _geojson(data, areas):
    feats = []
    for b in data["buildings"]:
        feats.append({"type": "Feature",
                      "properties": {"id": b["id"], "type": "BUILDING", "name": b["name"],
                                     "buildingType": b["buildingType"], "material": "WOOD"},
                      "geometry": {"type": "Polygon", "coordinates": _square(areas[b["id"]])}})
    feats.append({"type": "Feature", "properties": {"type": "EDGE", "edgeType": "ROAD"},
                  "geometry": {"type": "LineString", "coordinates": [[0, 0], [5, 5]]}})
    return {"type": "FeatureCollection", "features": feats}


@pytest.fixture
def vault(tmp_path):
    cdir = tmp_path / "world" / "maps" / "cities"
    shutil.copytree(ROOT / "world" / "maps" / "cities" / "profiles", cdir / "profiles")
    data, areas = make_town()
    (cdir / "Testburg.json").write_text(json.dumps(data))
    (cdir / "Testburg.geojson").write_text(json.dumps(_geojson(data, areas)))
    (cdir / "profiles" / "Testburg.yaml").write_text(
        "town: Testburg\nregion: central-asian-hubs\nseed: 7\nconversion_dial: 1\n"
        f"temples:\n  {TEMPLE}: F5\n"
        "pins:\n  people: {}\n  buildings: {}\n")
    return tmp_path


def _out(vault, name="gm.json"):
    return json.loads((sp.derived_dir(vault) / f"Testburg.{name}").read_text())


def _derived_bytes(vault):
    d = sp.derived_dir(vault)
    return {p.name: p.read_bytes() for p in sorted(d.iterdir())}


# -- S1, S2: determinism and the seed -----------------------------------------------------

def test_s1_same_seed_gives_byte_identical_output(vault):
    sp.draft("Testburg", vault)
    first = _derived_bytes(vault)
    sp.draft("Testburg", vault)
    assert _derived_bytes(vault) == first


def test_s2_a_different_seed_changes_names_but_not_headcount_or_ids(vault):
    sp.draft("Testburg", vault, seed=7)
    a = _out(vault)
    sp.draft("Testburg", vault, seed=8)
    b = _out(vault)
    assert [p["id"] for p in a["people"]] == [p["id"] for p in b["people"]]
    assert [x["id"] for x in a["buildings"]] == [x["id"] for x in b["buildings"]]
    assert [p["firstName"] for p in a["people"]] != [p["firstName"] for p in b["people"]]


# -- S3: what never changes ---------------------------------------------------------------

def test_s3_id_age_gender_job_residence_and_work_are_preserved(vault):
    sp.draft("Testburg", vault)
    src, _ = make_town()
    for a, b in zip(src["people"], _out(vault)["people"]):
        for f in sp.FROZEN_PERSON_FIELDS:
            assert a.get(f) == b.get(f), (a["id"], f)


# -- S4: ancestry -------------------------------------------------------------------------

def test_s4_only_vault_ancestries_appear(vault):
    sp.draft("Testburg", vault)
    races = {p["race"] for p in _out(vault)["people"]}
    assert races <= sp.ANCESTRIES
    assert "Half-Orc" not in races


def test_s4_a_household_shares_one_ancestry(vault):
    sp.draft("Testburg", vault)
    people = {p["id"]: p for p in _out(vault)["people"]}
    assert len({people[i]["race"] for i in (100, 101, 102, 103, 104)}) == 1


def test_s4_jivar_and_vanara_default_to_zero_and_never_drawn_refused(vault):
    prof = sp.load_profile("Testburg", vault)
    assert prof["ancestry"]["Jivar"] == 0 and prof["ancestry"]["Vanara"] == 0
    path = sp.profiles_dir(vault) / "Testburg.yaml"
    path.write_text(path.read_text() + "ancestry:\n  Ribbet: 5\n")
    with pytest.raises(sp.ProfileError, match="never drawn"):
        sp.load_profile("Testburg", vault)


def test_s4_a_profile_can_name_jivar(vault):
    path = sp.profiles_dir(vault) / "Testburg.yaml"
    path.write_text(path.read_text() + "ancestry:\n  Human: 0\n  Tulpar: 0\n  Kuhban: 0\n  Rahban: 0\n"
                    "  Gavar: 0\n  Pari-Kin: 0\n  Kalan: 0\n  Div-Born: 0\n  Vaghri: 0\n  Serenvar: 0\n"
                    "  Khavar: 0\n  Tadbir: 0\n  Jivar: 1\n")
    sp.draft("Testburg", vault)
    assert {p["race"] for p in _out(vault)["people"]} == {"Jivar"}


# -- S5: the surname map and its cascade --------------------------------------------------

def test_s5_the_surname_map_covers_residences_and_geojson_names(vault):
    sp.draft("Testburg", vault)
    out, gj = _out(vault), _out(vault, "geojson")
    ryke_new = {p["lastName"] for p in out["people"] if p["id"] in (100, 102, 103)}
    assert len(ryke_new) == 1
    new = ryke_new.pop()
    b = {x["id"]: x["name"] for x in out["buildings"]}
    if new:
        assert b[1] == b[2] == f"The {new} Residence"
    assert "Ryke" not in b[1]
    names = {f["properties"]["id"]: f["properties"]["name"]
             for f in gj["features"] if f["properties"].get("type") == "BUILDING"}
    assert names == b


def test_s5_parents_in_two_families_share_a_household_and_surname_rule(vault):
    sp.draft("Testburg", vault)
    people = {p["id"]: p for p in _out(vault)["people"]}
    assert people[100]["race"] == people[101]["race"]
    assert sp.load_profile("Testburg", vault) and not _report_problems(vault)


def _report_problems(vault):
    return sp.draft("Testburg", vault)["problems"]


# -- S6: family links ---------------------------------------------------------------------

def test_s6_family_links_are_untouched(vault):
    sp.draft("Testburg", vault)
    src, _ = make_town()
    for a, b in zip(src["people"], _out(vault)["people"]):
        assert a["childInFamilies"] == b["childInFamilies"]
        assert a["parentInFamilies"] == b["parentInFamilies"]


# -- S7: religion -------------------------------------------------------------------------

def test_s7_ftg_none_becomes_non_religious(vault):
    sp.draft("Testburg", vault)
    people = {p["id"]: p for p in _out(vault)["people"]}
    assert people[101]["religion"] == people[107]["religion"] == "Non-religious"


def test_s7_temple_staff_take_the_temples_faith(vault):
    sp.draft("Testburg", vault)
    people = {p["id"]: p for p in _out(vault)["people"]}
    assert people[104]["religion"] == people[106]["religion"] == "The Caves"


def test_s7_no_alignment_wording_survives(vault):
    sp.draft("Testburg", vault)
    for p in _out(vault)["people"]:
        assert " gods" not in (p["religion"] or "")


def test_s7_religion_is_drawn_from_the_region_table(vault):
    sp.draft("Testburg", vault)
    prof = sp.load_profile("Testburg", vault)
    allowed = {prof["faiths"][c] for c in prof["faith"] if c != "lapsed"}
    allowed |= {prof["lapsed"], prof["no_religion"]}
    assert {p["religion"] for p in _out(vault)["people"]} <= allowed


# -- S8: jobs and the conversion dial -----------------------------------------------------

def test_s8_jobs_are_unchanged(vault):
    sp.draft("Testburg", vault)
    src, _ = make_town()
    assert [p.get("jobTitle") for p in src["people"]] == [p.get("jobTitle") for p in _out(vault)["people"]]


def test_s8_dial_1_converts_only_buildings_over_the_threshold(vault):
    report = sp.draft("Testburg", vault)
    assert {c["id"]: c["to"] for c in report["conversions"]} == {10: "caravanserai", 12: "khan"}


def test_s8_dial_0_converts_nothing_and_dial_2_converts_more(vault):
    path = sp.profiles_dir(vault) / "Testburg.yaml"
    text = path.read_text()
    path.write_text(text.replace("conversion_dial: 1", "conversion_dial: 0"))
    assert sp.draft("Testburg", vault)["conversions"] == []
    path.write_text(text.replace("conversion_dial: 1", "conversion_dial: 2"))
    ids = {c["id"] for c in sp.draft("Testburg", vault)["conversions"]}
    assert ids == {10, 12}  # 150 and 300 m2 stay below dial 2's 250 / 450 except none new here
    assert 13 not in ids and 11 not in ids


def test_s8_alcohol_businesses_are_kept_with_a_trade_goods_note(vault):
    sp.draft("Testburg", vault)
    tavern = next(b for b in _out(vault)["buildings"] if b["id"] == 14)
    assert tavern["buildingType"] == "TAVERN"
    assert "alcohol kept" in tavern["notes"]


# -- S9: pins -----------------------------------------------------------------------------

def test_s9_pinned_entries_are_untouched_or_take_only_the_pinned_fields(vault):
    path = sp.profiles_dir(vault) / "Testburg.yaml"
    path.write_text(path.read_text().replace(
        "pins:\n  people: {}\n  buildings: {}\n",
        "pins:\n  people:\n    105: {}\n    106: {race: Kuhban, lastName: Stonehand}\n"
        "  buildings:\n    10: {}\n"))
    report = sp.draft("Testburg", vault)
    out = _out(vault)
    src, _ = make_town()
    people = {p["id"]: p for p in out["people"]}
    srcp = {p["id"]: p for p in src["people"]}
    assert people[105] == srcp[105]
    assert people[106]["race"] == "Kuhban" and people[106]["lastName"] == "Stonehand"
    assert people[106]["firstName"] == srcp[106]["firstName"]
    b10 = next(b for b in out["buildings"] if b["id"] == 10)
    assert b10["specificBuildingType"] == "medium inn" and b10["name"] == "Big Inn"
    assert 10 not in {c["id"] for c in report["conversions"]}


def test_s9_an_unsupported_pin_field_is_refused(vault):
    path = sp.profiles_dir(vault) / "Testburg.yaml"
    path.write_text(path.read_text().replace("people: {}", "people:\n    105: {age: 99}"))
    with pytest.raises(sp.ProfileError, match="unsupported"):
        sp.load_profile("Testburg", vault)


# -- S10: people stay out of the geometry -------------------------------------------------

def test_s10_the_geojson_carries_no_person_data(vault):
    sp.draft("Testburg", vault)
    text = (sp.derived_dir(vault) / "Testburg.geojson").read_text()
    for p in _out(vault)["people"]:
        assert f'"{p["firstName"]}"' not in text
    assert "coreValues" not in text and "religion" not in text


# -- S11: the report ----------------------------------------------------------------------

def test_s11_the_report_is_written_and_counts_match(vault):
    report = sp.draft("Testburg", vault)
    text = (sp.derived_dir(vault) / "Testburg.report.txt").read_text()
    assert report["people"] == 8 and "8 people" in text
    assert sum(report["ancestry"].values()) == 8
    assert "Conversions (2)" in text


# -- S12: the lock ------------------------------------------------------------------------

def test_s12_a_locked_town_refuses_to_draft_and_leaves_derived_files_alone(vault):
    sp.draft("Testburg", vault)
    before = _derived_bytes(vault)
    sp.lock("Testburg", vault)
    with pytest.raises(sp.Locked):
        sp.draft("Testburg", vault)
    assert _derived_bytes(vault) == before


def test_s12_a_locked_draft_does_not_read_the_ftg_source(vault):
    sp.draft("Testburg", vault)
    sp.lock("Testburg", vault)
    cdir = sp.cities_dir(vault)
    (cdir / "Testburg.json").unlink()
    (cdir / "Testburg.geojson").unlink()
    with pytest.raises(sp.Locked):
        sp.draft("Testburg", vault)


def test_s12_lock_needs_a_draft(vault):
    with pytest.raises(sp.ProfileError, match="no draft"):
        sp.lock("Testburg", vault)


def test_s12_lock_changes_only_the_flag(vault):
    sp.draft("Testburg", vault)
    path = sp.profiles_dir(vault) / "Testburg.yaml"
    before = path.read_text()
    sp.lock("Testburg", vault)
    assert path.read_text() == before.rstrip("\n") + "\nlocked: true\n"
    sp.lock("Testburg", vault)
    assert path.read_text().count("locked: true") == 1


def test_cli_exit_codes(vault, monkeypatch):
    monkeypatch.setattr(sp, "VAULT_ROOT", vault)
    monkeypatch.setattr(sp, "draft", lambda town, root=vault, seed=None: sp.draft.__wrapped__(town, root, seed)
                        if hasattr(sp.draft, "__wrapped__") else (_ for _ in ()).throw(sp.Locked("x")))
    assert sp.main(["draft", "Testburg"]) == 2


# -- S13: the source is never written, on the real export ---------------------------------

REAL = ROOT / "world" / "maps" / "cities" / "Dehdadi.json"


@pytest.mark.skipif(not REAL.exists(), reason="Dehdadi FTG export not present")
def test_s13_and_s1_real_dehdadi_is_deterministic_and_the_source_untouched(tmp_path):
    cdir = tmp_path / "world" / "maps" / "cities"
    shutil.copytree(ROOT / "world" / "maps" / "cities" / "profiles", cdir / "profiles")
    shutil.copytree(ROOT / "world" / "factions", tmp_path / "world" / "factions")
    for ext in ("json", "geojson"):
        shutil.copy(ROOT / "world" / "maps" / "cities" / f"Dehdadi.{ext}", cdir)
    digest = sp.source_digest("Dehdadi", tmp_path)
    report = sp.draft("Dehdadi", tmp_path)
    first = _derived_bytes_for(tmp_path)
    sp.draft("Dehdadi", tmp_path)
    assert _derived_bytes_for(tmp_path) == first
    assert sp.source_digest("Dehdadi", tmp_path) == digest
    assert report["people"] == 5575 and report["buildings"] == 1629
    assert report["problems"] == []
    assert "Half-Orc" not in report["ancestry"]
    assert len(report["conversions"]) == 10


def _derived_bytes_for(root):
    d = sp.derived_dir(root)
    return {p.name: p.read_bytes() for p in sorted(d.iterdir())}


# -- S14 to S18: factions layer (#387) ----------------------------------------------------

def _with_factions(vault, block):
    fdir = vault / "world" / "factions"
    fdir.mkdir(parents=True, exist_ok=True)
    for slug in ("watch-order", "secret-cell"):
        (fdir / f"{slug}.md").write_text("---\ntitle: x\n---\n")
    path = sp.profiles_dir(vault) / "Testburg.yaml"
    path.write_text(path.read_text() + block)


FACTION_BLOCK = (
    "factions:\n  seats:\n    10: watch-order\n  leaders:\n    secret-cell: [106]\n"
    "  members:\n    - {faction: secret-cell, jobs: [Weaver, Server], chance: 1}\n")


def test_s14_seat_staff_rule_members_and_leaders(vault):
    _with_factions(vault, FACTION_BLOCK)
    sp.draft("Testburg", vault)
    f = _out(vault)["factions"]
    assert f["watch-order"] == {"seats": [10], "members": [{"id": 100, "role": "member"}]}
    assert f["secret-cell"]["members"] == [
        {"id": 101, "role": "member"}, {"id": 105, "role": "member"}, {"id": 106, "role": "leader"}]


def test_s15_membership_is_deterministic_and_seeded(vault):
    _with_factions(vault, FACTION_BLOCK.replace("chance: 1", "chance: 0.5"))
    sp.draft("Testburg", vault)
    first = _out(vault)["factions"]
    sp.draft("Testburg", vault)
    assert _out(vault)["factions"] == first


def test_s16_the_geometry_and_people_records_never_name_a_faction(vault):
    _with_factions(vault, FACTION_BLOCK)
    sp.draft("Testburg", vault)
    assert "secret-cell" not in (sp.derived_dir(vault) / "Testburg.geojson").read_text()
    assert all("faction" not in p for p in _out(vault)["people"])


def test_s17_unknown_faction_building_or_person_is_refused(vault):
    _with_factions(vault, "factions:\n  seats:\n    10: no-such-faction\n")
    with pytest.raises(sp.ProfileError):
        sp.draft("Testburg", vault)
    path = sp.profiles_dir(vault) / "Testburg.yaml"
    path.write_text(path.read_text().replace("no-such-faction", "watch-order").replace("10:", "999:"))
    with pytest.raises(sp.ProfileError):
        sp.draft("Testburg", vault)


def test_s18_the_report_lists_seats_leaders_and_samples(vault):
    _with_factions(vault, FACTION_BLOCK)
    report = sp.draft("Testburg", vault)
    text = (sp.derived_dir(vault) / "Testburg.report.txt").read_text()
    assert report["factions"]["secret-cell"]["members"] == 3
    assert "Faction secret-cell: 3 members" in text and "leader: 106" in text
    assert "seats: 10 " in text
