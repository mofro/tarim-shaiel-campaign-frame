"""
Settlement profiles and cultural passes for Fantasy Town Generator (FTG) towns (#386).

An FTG town arrives as people and buildings with generic names, two races and three
alignment-flavoured religions. This module turns that source into a derived town for
Tarim-Shaiel, in two phases:

  DRAFT  re-runnable, seeded, deterministic: FTG source -> ordered passes -> derived files.
  LOCK   a per-town flag in the profile. Once set, draft refuses to run and the FTG files
         are never read again; the derived files are the town.

Passes, in order: ancestry (per household), names (file-wide surname map, cascaded into
residence names and GeoJSON `name`), family (checked, never rewritten), religion, jobs and
buildings (the conversion dial). Entries pinned by FTG id are skipped by every pass.
Headcount, ids, genders, jobs and residences never change; ages too, unless the profile
sets `rescale_ages` (see FTG_LIFESPAN).

People data goes only to the GM-only sidecar (`<Town>.gm.json`), never into the geometry.

Every random draw is keyed on its own subject (`seed:pass:id`), so a draw does not depend
on the order of the others and a different seed changes names without moving a headcount.

Usage:
    venv/bin/python utilities/geojson/settlement_profiles.py draft Dehdadi [--seed N]
    venv/bin/python utilities/geojson/settlement_profiles.py lock Dehdadi
"""

import argparse
import hashlib
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

VAULT_ROOT = Path(__file__).parent.parent.parent

CITIES = ("world", "maps", "cities")

# Vault ancestry names (Human, plus the epic's mapping of the FTG/Daggerheart list).
ANCESTRIES = frozenset({
    "Human", "Tulpar", "Kuhban", "Rahban", "Gavar", "Pari-Kin", "Kalan", "Div-Born",
    "Vaghri", "Serenvar", "Khavar", "Tadbir", "Jivar", "Vanara",
})
# Never drawn, whatever a profile says.
NEVER_DRAWN = frozenset({"Naga-Kin", "Faerie", "Galapa", "Ribbet"})

# Ages (#406 case 4). FTG draws each age on the scale of the person's ORIGINAL FTG race; the
# ancestry pass then changes the race, so an Elf's 400 can land on a Human. With
# `rescale_ages: true` a person keeps their place in the life (age / FTG lifespan, capped at 1)
# and takes the age that place has in the new ancestry's lifespan (PEOPLES_OF_TARIM_SHAIEL.md).
FTG_LIFESPAN = {"Human": 100, "Half-Orc": 75, "Tiefling": 100, "Dragonborn": 80, "Half-Elf": 180,
                "Dwarf": 350, "Halfling": 250, "Gnome": 400, "Elf": 750}
LIFESPAN = {"Human": 100, "Serenvar": 350, "Kuhban": 250, "Tulpar": 125, "Khavar": 300, "Vaghri": 150,
            "Jivar": 100, "Rahban": 150, "Kalan": 75, "Vanara": 150, "Gavar": 100, "Div-Born": 500}
# No figure (or no limit) in the ancestry docs: ages kept as FTG drew them. Tadbir are not
# bounded by years; Pari-Kin have no stated lifespan.
UNSCALED = frozenset({"Tadbir", "Pari-Kin"})
PARENT_GAP = 0.15  # a parent is at least this share of a lifespan older than a child

PERSON_PIN_FIELDS = frozenset({"race", "firstName", "lastName", "religion"})
BUILDING_PIN_FIELDS = frozenset({"name", "specificBuildingType"})


class ProfileError(ValueError):
    """The profile is missing, malformed or names something the pipeline refuses."""


class Locked(RuntimeError):
    """The town is locked: the draft phase refuses to run."""


# -- paths ---------------------------------------------------------------------------

def cities_dir(root: Path = VAULT_ROOT) -> Path:
    return root.joinpath(*CITIES)


def profiles_dir(root: Path = VAULT_ROOT) -> Path:
    return cities_dir(root) / "profiles"


def derived_dir(root: Path = VAULT_ROOT) -> Path:
    return cities_dir(root) / "derived"


# -- profile loader ------------------------------------------------------------------

def deep_merge(base: dict, over: dict) -> dict:
    """Mappings merge key by key; everything else in `over` replaces."""
    out = dict(base)
    for key, val in over.items():
        if isinstance(val, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], val)
        else:
            out[key] = val
    return out


def _read_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except FileNotFoundError:
        raise ProfileError(f"missing profile layer: {path}")
    except yaml.YAMLError as exc:
        raise ProfileError(f"{path.name}: {exc}")
    if not isinstance(data, dict):
        raise ProfileError(f"{path.name}: top level must be a mapping")
    return data


def load_profile(town: str, root: Path = VAULT_ROOT) -> dict:
    """_defaults.yaml, then <region>.yaml, then <Town>.yaml, merged in that order."""
    pdir = profiles_dir(root)
    town_layer = _read_yaml(pdir / f"{town}.yaml")
    region = town_layer.get("region")
    if not region:
        raise ProfileError(f"{town}.yaml: `region:` is required")
    profile = deep_merge(_read_yaml(pdir / "_defaults.yaml"), _read_yaml(pdir / f"{region}.yaml"))
    profile = deep_merge(profile, town_layer)
    profile["town"] = town
    validate_profile(profile)
    return profile


def validate_profile(profile: dict) -> None:
    banned = [a for a, w in profile["ancestry"].items() if a in NEVER_DRAWN and w]
    if banned:
        raise ProfileError(f"never drawn, remove from `ancestry`: {', '.join(sorted(banned))}")
    unknown = [a for a in profile["ancestry"] if a not in ANCESTRIES and a not in NEVER_DRAWN]
    if unknown:
        raise ProfileError(f"unknown ancestry: {', '.join(sorted(unknown))}")
    if not any(w > 0 for w in profile["ancestry"].values()):
        raise ProfileError("`ancestry` has no positive weight")
    if profile.get("conversion_dial") not in (0, 1, 2):
        raise ProfileError("`conversion_dial` must be 0, 1 or 2")
    for code in profile.get("faith", {}):
        if code not in profile["faiths"] and code != "lapsed":
            raise ProfileError(f"faith share names an unknown faith: {code}")
    for code in (profile.get("temples") or {}).values():
        if code not in profile["faiths"]:
            raise ProfileError(f"temple names an unknown faith: {code}")
    pins = profile.get("pins") or {}
    for kind, allowed in (("people", PERSON_PIN_FIELDS), ("buildings", BUILDING_PIN_FIELDS)):
        for pid, fields in (pins.get(kind) or {}).items():
            bad = set(fields or {}) - allowed
            if bad:
                raise ProfileError(f"pins.{kind}.{pid}: unsupported field(s) {', '.join(sorted(bad))}")
    for pid, fields in (pins.get("people") or {}).items():
        race = (fields or {}).get("race")
        if race is not None and (race in NEVER_DRAWN or race not in ANCESTRIES):
            raise ProfileError(f"pins.people.{pid}: {race} is not a drawable ancestry")


# -- seeded draws --------------------------------------------------------------------

def rng_for(seed, *key) -> random.Random:
    """A generator for one subject. Seeded from text, so it is stable across runs."""
    return random.Random(":".join(str(k) for k in (seed, *key)))


def weighted(rng: random.Random, weights: dict):
    items = sorted((k, w) for k, w in weights.items() if w > 0)
    total = sum(w for _, w in items)
    pick = rng.random() * total
    for key, w in items:
        pick -= w
        if pick < 0:
            return key
    return items[-1][0]


# -- source --------------------------------------------------------------------------

def read_source(town: str, root: Path = VAULT_ROOT) -> tuple[dict, dict]:
    """(people/buildings json, geojson). Read-only: the FTG files are never written."""
    cdir = cities_dir(root)
    with open(cdir / f"{town}.json", encoding="utf-8") as fh:
        data = json.load(fh)
    with open(cdir / f"{town}.geojson", encoding="utf-8") as fh:
        gj = json.load(fh)
    return data, gj


def polygon_area(ring) -> float:
    n = len(ring)
    return abs(sum(ring[i][0] * ring[(i + 1) % n][1] - ring[(i + 1) % n][0] * ring[i][1]
                   for i in range(n))) / 2


def building_areas(gj: dict) -> dict:
    """FTG building id -> footprint in m2 (the export is in local metres)."""
    out = {}
    for feat in gj["features"]:
        props = feat["properties"]
        if props.get("type") == "BUILDING" and feat["geometry"]["type"] == "Polygon":
            out[props["id"]] = polygon_area(feat["geometry"]["coordinates"][0])
    return out


def households(people: list) -> dict:
    """person id -> household id. A household is everyone linked by a shared residence or
    a shared family (a parent can sit in two families), so a family never splits."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for p in people:
        find(("p", p["id"]))
        if p.get("placeOfResidence") is not None:
            parent[find(("p", p["id"]))] = find(("b", p["placeOfResidence"]))
        for fam in p.get("childInFamilies", []) + p.get("parentInFamilies", []):
            parent[find(("p", p["id"]))] = find(("f", fam))
    groups = {}
    for p in people:
        groups.setdefault(find(("p", p["id"])), []).append(p["id"])
    return {pid: min(ids) for ids in groups.values() for pid in ids}


# -- passes --------------------------------------------------------------------------

def _pins(profile: dict, kind: str) -> dict:
    return {int(k): (v or {}) for k, v in ((profile.get("pins") or {}).get(kind) or {}).items()}


def ancestry_pass(profile, seed, hh) -> dict:
    """household id -> ancestry. One draw per household, so a family shares an ancestry."""
    weights = {a: w for a, w in profile["ancestry"].items() if a not in NEVER_DRAWN}
    return {h: weighted(rng_for(seed, "ancestry", h), weights) for h in sorted(set(hh.values()))}


UNIQUE_TRIES = 60


class Namer:
    """Names for one town. Surnames are one file-wide map keyed on (FTG surname, ancestry)."""

    def __init__(self, profile, seed):
        self.profile, self.seed = profile, seed
        self.region = profile["names"]
        self.by_ancestry = profile["ancestry_names"]
        self.surnames = {}
        self.family_use = {}

    def pool(self, gender, ancestry):
        own = (self.by_ancestry.get(ancestry) or {}).get("given")
        if own:
            return own
        return self.region[gender] if gender in ("male", "female") else self.region["male"] + self.region["female"]

    def given(self, person_id, gender, ancestry, attempt=0):
        """Attempt 0 is the person's own draw. Later attempts are retries for a repeated full
        name: the first half stay in the ancestry's pool, the rest widen to the region's pool."""
        key = ("given", person_id) if not attempt else ("given", person_id, attempt)
        pool = self.pool(gender, ancestry) if attempt < UNIQUE_TRIES // 2 else (
            self.region[gender] if gender in ("male", "female") else self.region["male"] + self.region["female"])
        return rng_for(self.seed, *key).choice(pool)

    def surname(self, original, ancestry):
        if not original:
            return original
        key = (original, ancestry)
        if key not in self.surnames:
            self.surnames[key] = self._draw_surname(original, ancestry)
        return self.surnames[key]

    def personal(self, person_id, ancestry):
        """A patronymic for someone FTG gave no family name and whose household has none."""
        if (self.by_ancestry.get(ancestry) or {}).get("single"):
            return ""
        rng = rng_for(self.seed, "personal", person_id)
        return rng.choice(self.region["male"]) + rng.choice(self.region["patronymic_suffixes"])

    def _draw_surname(self, original, ancestry):
        rng = rng_for(self.seed, "surname", original, ancestry)
        mod = self.by_ancestry.get(ancestry) or {}
        if mod.get("single"):
            return ""
        if mod.get("family"):
            # spread the ancestry's family names evenly: take one of the least used so far
            used = self.family_use.setdefault(ancestry, Counter())
            low = min(used[n] for n in mod["family"])
            name = rng.choice([n for n in mod["family"] if used[n] == low])
            used[name] += 1
            return name
        form = weighted(rng, self.region["family_forms"])
        if form == "patronymic":
            return rng.choice(self.region["male"]) + rng.choice(self.region["patronymic_suffixes"])
        return rng.choice(self.region["lineages"])

    def informal(self, person_id):
        rng = rng_for(self.seed, "informal", person_id)
        if rng.random() < self.profile["informal_byname_share"]:
            return rng.choice(self.profile["informal_bynames"])
        return None


def faith_name(profile, code):
    return profile["lapsed"] if code == "lapsed" else profile["faiths"][code]


def religion_pass(profile, seed, people, hh, ancestry_of_hh, pinned) -> dict:
    """person id -> religion string. FTG None stays non-religious; staff of a temple take its
    faith; everyone else draws from the region's table, mostly following their household."""
    temples = {int(k): v for k, v in (profile.get("temples") or {}).items()}
    table = profile["faith"]
    out = {}
    for p in sorted(people, key=lambda q: q["id"]):
        pid = p["id"]
        if pid in pinned:
            continue
        if p.get("religion") is None:
            out[pid] = profile["no_religion"]
            continue
        if p.get("placeOfWork") in temples:
            out[pid] = faith_name(profile, temples[p["placeOfWork"]])
            continue
        pulls = profile["faith_pulls"].get(ancestry_of_hh[hh[pid]], {})
        weights = {c: w * pulls.get(c, 1) for c, w in table.items()}
        home = weighted(rng_for(seed, "faith", hh[pid]), weights)
        own = rng_for(seed, "faith-person", pid)
        code = home if own.random() < profile["household_faith_keep"] else weighted(own, weights)
        out[pid] = faith_name(profile, code)
    return out


def validate_factions(profile, people, buildings, root: Path) -> None:
    """The `factions:` block (#387) may only name faction files, buildings and people that exist."""
    cfg = profile.get("factions") or {}
    bids, pids = {b["id"] for b in buildings}, {p["id"] for p in people}
    slugs = set(cfg.get("seats", {}).values())
    slugs |= {r.get("faction") for r in cfg.get("members") or []} | set(cfg.get("leaders") or {})
    for slug in sorted(slugs, key=str):
        if not slug or not (root / "world" / "factions" / f"{slug}.md").exists():
            raise ProfileError(f"factions: no faction file world/factions/{slug}.md")
    for bid in cfg.get("seats", {}):
        if int(bid) not in bids:
            raise ProfileError(f"factions.seats: no building {bid}")
    for slug, ids in (cfg.get("leaders") or {}).items():
        for pid in ids or []:
            if pid not in pids:
                raise ProfileError(f"factions.leaders.{slug}: no person {pid}")
    for rule in cfg.get("members") or []:
        if not 0 <= rule.get("chance", 1) <= 1:
            raise ProfileError(f"factions.members: chance must be 0 to 1 ({rule.get('faction')})")


def faction_pass(profile, seed, people) -> dict:
    """Membership for the GM-only sidecar. Staff of a seat belong to its faction; a rule adds
    people by job title with a seeded chance; named leaders are marked. A person can belong to
    several factions. Never touches a person record."""
    cfg = profile.get("factions") or {}
    seats = {int(b): slug for b, slug in (cfg.get("seats") or {}).items()}
    leaders = {(slug, pid) for slug, ids in (cfg.get("leaders") or {}).items() for pid in ids or []}
    roles = {}
    for p in people:
        pid = p["id"]
        if seats.get(p.get("placeOfWork")):
            roles.setdefault(seats[p["placeOfWork"]], {})[pid] = "member"
        for rule in cfg.get("members") or []:
            slug = rule["faction"]
            if p.get("jobTitle") in rule.get("jobs", []) and \
                    rng_for(seed, "faction", slug, pid).random() < rule.get("chance", 1):
                roles.setdefault(slug, {}).setdefault(pid, "member")
    for slug, pid in leaders:
        roles.setdefault(slug, {})[pid] = "leader"
    by_slug = {}
    for bid, slug in sorted(seats.items()):
        by_slug.setdefault(slug, []).append(bid)
    return {slug: {"seats": by_slug.get(slug, []),
                   "members": [{"id": pid, "role": r} for pid, r in sorted(roles.get(slug, {}).items())]}
            for slug in sorted(set(by_slug) | set(roles))}


def conversion_pass(profile, buildings, areas, pinned) -> dict:
    """building id -> specificBuildingType for buildings the dial converts."""
    dial = profile["conversion_dial"]
    if not dial:
        return {}
    limits = profile["conversion"][dial]
    out = {}
    for b in buildings:
        kind = b["buildingType"]
        if b["id"] in pinned or kind not in limits or kind not in profile["converts_to"]:
            continue
        if areas.get(b["id"], 0) >= limits[kind]:
            out[b["id"]] = profile["converts_to"][kind]
    return out


# -- draft ---------------------------------------------------------------------------

def rename_building(name, namer, known, ancestry_for):
    """Replace a residence's surname, or any word that is a known FTG surname."""
    m = re.fullmatch(r"The (.+) Residence", name)
    if m:
        new = namer.surname(m.group(1), ancestry_for(m.group(1)))
        return f"The {new} Residence" if new else "The Residence"
    return " ".join(
        (namer.surname(w, ancestry_for(w)) or w) if w in known else w for w in name.split(" "))


def draft(town: str, root: Path = VAULT_ROOT, seed=None) -> dict:
    """Run the passes and write derived/<Town>.geojson, .gm.json and .report.txt.

    Returns the report as a dict. Raises Locked before reading any FTG file.
    """
    profile = load_profile(town, root)
    if profile.get("locked"):
        raise Locked(f"{town} is locked; the derived files are the town. "
                     f"Set `locked: false` in its profile to draft again.")
    seed = profile["seed"] if seed is None else seed
    data, gj = read_source(town, root)
    people, buildings = data["people"], data["buildings"]
    areas = building_areas(gj)
    ppins, bpins = _pins(profile, "people"), _pins(profile, "buildings")

    hh = households(people)
    anc_of_hh = ancestry_pass(profile, seed, hh)
    namer = Namer(profile, seed)
    known = {p["lastName"] for p in people if p.get("lastName")}

    # the ancestry a surname most often belongs to, for buildings that name no household
    holders = {}
    for p in people:
        holders.setdefault(p["lastName"], Counter())[anc_of_hh[hh[p["id"]]]] += 1
    primary = {s: sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for s, c in holders.items()}

    validate_factions(profile, people, buildings, root)
    factions = faction_pass(profile, seed, people)
    religion = religion_pass(profile, seed, people, hh, anc_of_hh, ppins)
    converted = conversion_pass(profile, buildings, areas, bpins)

    # one surname per household, for the children and unattached adults FTG left blank
    counts = {}
    for p in people:
        if p["lastName"]:
            counts.setdefault(hh[p["id"]], Counter())[p["lastName"]] += 1
    house_surname = {h: sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for h, c in counts.items()}
    # full names already fixed by pins, so a drawn name never repeats one
    taken = {(ppins[p["id"]].get("firstName", p["firstName"]), ppins[p["id"]].get("lastName", p["lastName"]))
             for p in people if p["id"] in ppins}
    out_people, ancestry_of = [], {}
    for p in people:
        q = dict(p)
        pid = p["id"]
        if pid in ppins:
            q.update(ppins[pid])
        else:
            anc = anc_of_hh[hh[pid]]
            q["race"] = anc
            original = p["lastName"] or house_surname.get(hh[pid], "")
            last = namer.surname(original, anc) if original else namer.personal(pid, anc)
            first = namer.given(pid, p.get("gender"), anc)
            for attempt in range(1, UNIQUE_TRIES):
                if (first, last) not in taken:
                    break
                first = namer.given(pid, p.get("gender"), anc, attempt)
            taken.add((first, last))
            q["firstName"], q["lastName"] = first, last
            q["religion"] = religion[pid]
            informal = namer.informal(pid)
            if informal:
                q["informalByname"] = informal
        ancestry_of[pid] = q["race"]
        out_people.append(q)
    if profile.get("rescale_ages"):
        rescale_ages(people, out_people, ppins)

    # residents decide a residence's ancestry
    res_anc = {}
    for p in sorted(people, key=lambda q: q["id"]):
        if p.get("placeOfResidence") is not None:
            res_anc.setdefault(p["placeOfResidence"], ancestry_of[p["id"]])

    out_buildings, new_names = [], {}
    for b in buildings:
        c = dict(b)
        bid = b["id"]
        if bid in bpins:
            c.update(bpins[bid])
        else:
            c["name"] = rename_building(
                b["name"], namer, known, lambda s, bid=bid: res_anc.get(bid) or primary.get(s, "Human"))
            note = (b.get("notes") or "").strip()
            if bid in converted:
                c["specificBuildingType"] = converted[bid]
                note = f"{note} Converted by settlement profile from {b['specificBuildingType']}.".strip()
            if b["buildingType"] in ("TAVERN", "INN") and b.get("specificBuildingType") in profile["alcohol_types"]:
                note = f"{note} {profile['alcohol_note']}".strip()
            if note != (b.get("notes") or "").strip():
                c["notes"] = note
            if profile.get("medieval_hours"):
                apply_hours(c, profile["hours"])
        new_names[bid] = c["name"]
        out_buildings.append(c)

    # geometry: names (and conversions) only; nothing about people
    out_gj = json.loads(json.dumps(gj))
    for feat in out_gj["features"]:
        props = feat["properties"]
        if props.get("type") == "BUILDING" and props.get("id") in new_names:
            props["name"] = new_names[props["id"]]
            if props["id"] in converted:
                props["kind"] = converted[props["id"]]

    retitled = retitle_people(profile, converted, out_people, ppins) if profile.get("medieval_hours") else set()
    problems = check_derived(people, out_people, buildings, out_buildings, ppins,
                             ages_rescaled=bool(profile.get("rescale_ages")), retitled=retitled)
    report = make_report(profile, seed, out_people, out_buildings, areas, converted, namer, ppins, bpins, problems)
    report["factions"] = faction_report(factions, out_people, out_buildings, hh)

    ddir = derived_dir(root)
    ddir.mkdir(parents=True, exist_ok=True)
    _write_json(ddir / f"{town}.geojson", out_gj)
    _write_json(ddir / f"{town}.gm.json", {"town": town, "seed": seed, "buildings": out_buildings, "people": out_people,
                                                 "factions": factions})
    (ddir / f"{town}.report.txt").write_text(render_report(report), encoding="utf-8")
    return report


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# -- checks and report ---------------------------------------------------------------

FROZEN_PERSON_FIELDS = ("id", "age", "gender", "jobTitle", "placeOfWork", "placeOfResidence",
                        "childInFamilies", "parentInFamilies")


def apply_hours(b: dict, table: dict) -> None:
    """Swap an FTG openingTimes for the template of the building's current type (see hours)."""
    if not b.get("openingTimes"):
        return
    t = table["types"].get(b.get("specificBuildingType")) or table["categories"].get(b["buildingType"])
    if not t:
        return
    if t.get("round_clock"):
        del b["openingTimes"]
    else:
        b["openingTimes"] = {"closedDays": list(t["closed"]), "openHour": t["open"], "closeHour": t["close"]}


def retitle_people(profile, converted, out_people, pinned) -> set:
    """Give staff of converted buildings the job title that fits (profile `retitle`). Returns ids."""
    changed = set()
    for q in out_people:
        rules = profile["retitle"].get(converted.get(q.get("placeOfWork")))
        new = (rules or {}).get(q.get("jobTitle"))
        if new is None or q["id"] in pinned:
            continue
        q["jobTitle"] = new[q["id"] % len(new)] if isinstance(new, list) else new
        changed.add(q["id"])
    return changed


def rescale_ages(src_people, out_people, pinned) -> None:
    """Rewrite `age` in out_people in place; see FTG_LIFESPAN. Pinned people keep their age."""
    src = {p["id"]: p for p in src_people}
    for q in out_people:
        if q["id"] in pinned or q["race"] in UNSCALED or q["race"] not in LIFESPAN:
            continue
        scale = FTG_LIFESPAN.get(src[q["id"]].get("race"))
        if scale:
            q["age"] = round(min(1.0, src[q["id"]]["age"] / scale) * LIFESPAN[q["race"]])
    # a child must stay younger than every parent by PARENT_GAP of the parent's lifespan
    by_id = {q["id"]: q for q in out_people}
    parents = {}
    for q in out_people:
        for f in q.get("parentInFamilies") or []:
            parents.setdefault(f, []).append(q["id"])
    def gap_of(par):
        return round(PARENT_GAP * LIFESPAN.get(par["race"], 100))

    # pass 1, bottom-up: the youngest a parent can be is one gap above their child's youngest
    floor = {q["id"]: 0 for q in out_people}
    for _ in range(len(out_people)):
        moved = False
        for q in out_people:
            for f in q.get("childInFamilies") or []:
                for pid in parents.get(f, []):
                    need = floor[q["id"]] + gap_of(by_id[pid])
                    if need > floor[pid]:
                        floor[pid] = need
                        moved = True
        if not moved:
            break
    for q in out_people:
        if q["id"] not in pinned and q["age"] < floor[q["id"]]:
            q["age"] = floor[q["id"]]
    # pass 2, top-down: a child comes down to one gap below each parent, never under 0
    for _ in range(len(out_people)):
        moved = False
        for q in out_people:
            if q["id"] in pinned:
                continue
            for f in q.get("childInFamilies") or []:
                for pid in parents.get(f, []):
                    par = by_id[pid]
                    if q["age"] > par["age"] - gap_of(par):
                        q["age"] = max(0, par["age"] - gap_of(par))
                        moved = True
        if not moved:
            break


def check_derived(src_people, out_people, src_buildings, out_buildings, pinned, ages_rescaled=False, retitled=()) -> list:
    """What a draft must not change, and the family-name rule. Returns problem strings."""
    problems = []
    if len(src_people) != len(out_people) or len(src_buildings) != len(out_buildings):
        problems.append("headcount changed")
    for a, b in zip(src_people, out_people):
        for f in FROZEN_PERSON_FIELDS:
            if (f == "age" and ages_rescaled) or (f == "jobTitle" and a["id"] in retitled):
                continue
            if a.get(f) != b.get(f):
                problems.append(f"person {a['id']}: {f} changed")
    for a, b in zip(src_buildings, out_buildings):
        if a["id"] != b["id"] or a["buildingType"] != b["buildingType"]:
            problems.append(f"building {a['id']}: id or type changed")
    # one FTG surname + one ancestry -> one new surname, so no family splits
    seen = {}
    for a, b in zip(src_people, out_people):
        if a["id"] in pinned or not a["lastName"]:
            continue
        key = (a["lastName"], b["race"])
        if seen.setdefault(key, b["lastName"]) != b["lastName"]:
            problems.append(f"surname {key[0]} maps to two names for {key[1]}")
    for b in out_people:
        if b["race"] == "Half-Orc" or b["race"] in NEVER_DRAWN:
            problems.append(f"person {b['id']}: ancestry {b['race']}")
    return problems


def make_report(profile, seed, people, buildings, areas, converted, namer, ppins, bpins, problems) -> dict:
    return {
        "town": profile["town"],
        "seed": seed,
        "people": len(people),
        "buildings": len(buildings),
        "ancestry": dict(sorted(Counter(p["race"] for p in people).items())),
        "religion": dict(sorted(Counter(p["religion"] for p in people if p.get("religion")).items())),
        "surnames_mapped": len(namer.surnames),
        "conversions": [
            {"id": b["id"], "name": b["name"], "area_m2": round(areas.get(b["id"], 0)),
             "to": converted[b["id"]]}
            for b in buildings if b["id"] in converted],
        "pinned_people": sorted(ppins),
        "pinned_buildings": sorted(bpins),
        "problems": problems,
    }


def faction_report(factions, people, buildings, hh) -> dict:
    """What the GM compares against FTG: seats, leaders, counts, a few named members."""
    by_pid = {p["id"]: p for p in people}
    by_bid = {b["id"]: b for b in buildings}

    def line(pid):
        p = by_pid[pid]
        work = by_bid.get(p.get("placeOfWork"), {}).get("name", "no workplace")
        home = by_bid.get(p.get("placeOfResidence"), {}).get("name", "no residence")
        return (f"{pid} {p['firstName']} {p['lastName']}, {p.get('jobTitle') or 'no job'}, "
                f"works at {work}, lives at {home} (household {hh[pid]})")

    out = {}
    for slug, f in factions.items():
        ids = [m["id"] for m in f["members"]]
        out[slug] = {
            "seats": [f"{b} {by_bid[b]['name']}" for b in f["seats"]],
            "leaders": [line(m["id"]) for m in f["members"] if m["role"] == "leader"],
            "members": len(ids),
            "sample": [line(i) for i in ids[:3]],
        }
    return out


def render_report(r: dict) -> str:
    lines = [f"Settlement draft: {r['town']} (seed {r['seed']})",
             f"{r['people']} people, {r['buildings']} buildings, {r['surnames_mapped']} surname mappings", "",
             "Ancestry"]
    lines += [f"  {k}: {v}" for k, v in r["ancestry"].items()]
    lines += ["", "Religion"] + [f"  {k}: {v}" for k, v in r["religion"].items()]
    lines += ["", f"Conversions ({len(r['conversions'])})"]
    lines += [f"  {c['id']} {c['name']} ({c['area_m2']} m2) -> {c['to']}" for c in r["conversions"]]
    lines += ["", f"Pinned people: {r['pinned_people'] or 'none'}",
              f"Pinned buildings: {r['pinned_buildings'] or 'none'}"]
    for slug, f in r.get("factions", {}).items():
        lines += ["", f"Faction {slug}: {f['members']} members",
                  f"  seats: {', '.join(f['seats']) or 'none'}"]
        lines += [f"  leader: {x}" for x in f["leaders"]] + [f"  e.g. {x}" for x in f["sample"]]
    if r["problems"]:
        lines += ["", f"Problems ({len(r['problems'])})"] + [f"  {p}" for p in r["problems"][:50]]
    return "\n".join(lines) + "\n"


# -- lock ----------------------------------------------------------------------------

def lock(town: str, root: Path = VAULT_ROOT) -> None:
    """Set `locked: true` in the town's profile. Requires a draft to lock."""
    if not (derived_dir(root) / f"{town}.gm.json").exists():
        raise ProfileError(f"{town} has no draft to lock; run draft first")
    path = profiles_dir(root) / f"{town}.yaml"
    text = path.read_text(encoding="utf-8")
    if re.search(r"^locked:", text, re.M):
        text = re.sub(r"^locked:.*$", "locked: true", text, count=1, flags=re.M)
    else:
        text = text.rstrip("\n") + "\nlocked: true\n"
    path.write_text(text, encoding="utf-8")


def source_digest(town: str, root: Path = VAULT_ROOT) -> str:
    """Hash of the two FTG files, for the check that a run never touches them."""
    h = hashlib.sha256()
    for ext in ("json", "geojson"):
        h.update((cities_dir(root) / f"{town}.{ext}").read_bytes())
    return h.hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Draft or lock an FTG settlement (#386).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draft")
    d.add_argument("town")
    d.add_argument("--seed", type=int)
    lk = sub.add_parser("lock")
    lk.add_argument("town")
    args = ap.parse_args(argv)
    try:
        if args.cmd == "draft":
            sys.stdout.write(render_report(draft(args.town, seed=args.seed)))
        else:
            lock(args.town)
            print(f"{args.town} locked")
    except (ProfileError, Locked) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
