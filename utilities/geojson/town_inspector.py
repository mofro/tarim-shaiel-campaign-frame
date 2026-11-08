"""
GM-only town inspector data (#399).

Reads a drafted town's derived files (`world/maps/cities/derived/<Town>.geojson` and
`.gm.json`) and, when the FTG export is still present, its source building and people
records, so the GM can click a building and compare it with what Fantasy Town Generator
shows. Served by `utilities/devserver.py` at `/town/<Town>` and `/api/town/<Town>`, to
localhost only. Nothing here writes to `docs/`, so no player build can carry it.
"""

import json
import re
from pathlib import Path

try:
    from geojson import settlement_profiles as sp
except ImportError:  # run with utilities/geojson itself on the path, as the tests do
    import settlement_profiles as sp

PAGE_PATH = Path(__file__).with_name("town_inspector.html")
TOWN_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,40}$")


class NoSuchTown(Exception):
    """The town name is malformed, or it has no derived draft."""


def _read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load(town: str, root: Path = sp.VAULT_ROOT) -> dict:
    """{town, geojson, buildings, people, factions, source}. `source` holds the FTG
    building and people records keyed by id, or is empty once the town is locked and the
    export is gone. Raises NoSuchTown for a bad name or a town with no draft."""
    if not TOWN_RE.match(town):
        raise NoSuchTown(town)
    ddir = sp.derived_dir(root)
    gj_path, gm_path = ddir / f"{town}.geojson", ddir / f"{town}.gm.json"
    if not gj_path.is_file() or not gm_path.is_file():
        raise NoSuchTown(town)
    gm = _read(gm_path)
    src_path = sp.cities_dir(root) / f"{town}.json"
    source = {}
    if src_path.is_file():
        src = _read(src_path)
        source = {"buildings": {b["id"]: b for b in src["buildings"]},
                  "people": {p["id"]: p for p in src["people"]}}
    return {"town": town, "geojson": _read(gj_path), "buildings": gm["buildings"],
            "people": gm["people"], "factions": gm.get("factions", {}), "source": source}


def payload(town: str, root: Path = sp.VAULT_ROOT) -> dict:
    """The JSON the page loads: geometry plus, per building id, its record, its seat
    factions, and who works and lives there (ids only; the page looks people up)."""
    d = load(town, root)
    seats: dict[int, list[str]] = {}
    for slug, f in d["factions"].items():
        for b in f.get("seats", []):
            seats.setdefault(b, []).append(slug)
    member_of: dict[int, list[str]] = {}
    for slug, f in d["factions"].items():
        for m in f.get("members", []):
            member_of.setdefault(m["id"], []).append(f"{slug} ({m['role']})")
    works: dict[int, list[int]] = {}
    lives: dict[int, list[int]] = {}
    for p in d["people"]:
        if p.get("placeOfWork") is not None:
            works.setdefault(p["placeOfWork"], []).append(p["id"])
        if p.get("placeOfResidence") is not None:
            lives.setdefault(p["placeOfResidence"], []).append(p["id"])
    src_b = d["source"].get("buildings", {})
    src_p = d["source"].get("people", {})
    buildings = {}
    for b in d["buildings"]:
        bid = b["id"]
        s = src_b.get(bid)
        buildings[bid] = {**b, "seats": seats.get(bid, []), "works": works.get(bid, []),
                          "lives": lives.get(bid, []),
                          "hours": b.get("openingTimes"),
                          "ftg": {"name": s["name"], "type": s.get("specificBuildingType")} if s else None}
    # FTG stores family links as family ids only: the parents of a family are the people
    # whose parentInFamilies holds it, its children those whose childInFamilies holds it.
    fam_parents: dict[int, list[int]] = {}
    fam_kids: dict[int, list[int]] = {}
    for p in d["people"]:
        for f in p.get("parentInFamilies", []):
            fam_parents.setdefault(f, []).append(p["id"])
        for f in p.get("childInFamilies", []):
            fam_kids.setdefault(f, []).append(p["id"])

    def kin(p, own_key, table, skip_self=False):
        ids = [i for f in p.get(own_key, []) for i in table.get(f, []) if not (skip_self and i == p["id"])]
        return list(dict.fromkeys(ids))

    people = {}
    for p in d["people"]:
        s = src_p.get(p["id"])
        people[p["id"]] = {
            "id": p["id"], "name": f"{p['firstName']} {p['lastName']}", "age": p.get("age"),
            "gender": p.get("gender"), "race": p.get("race"), "religion": p.get("religion"),
            "job": p.get("jobTitle"), "work": p.get("placeOfWork"), "home": p.get("placeOfResidence"),
            "study": p.get("placeOfStudy"), "trait": p.get("relaxingTrait"),
            "core": p.get("coreValues"), "stats": p.get("stats"),
            "height": (p.get("appearance") or {}).get("heightCm"), "notes": p.get("notes") or None,
            "factions": member_of.get(p["id"], []),
            "parents": kin(p, "childInFamilies", fam_parents),
            "siblings": kin(p, "childInFamilies", fam_kids, skip_self=True),
            "children": kin(p, "parentInFamilies", fam_kids),
            "ftg": {"name": f"{s['firstName']} {s['lastName']}", "race": s.get("race"),
                    "religion": s.get("religion")} if s else None}
    return {"town": town, "locked_source": not src_b, "geojson": d["geojson"],
            "buildings": buildings, "people": people}
