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
Headcount, ids, ages, genders, jobs and residences never change.

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


class Namer:
    """Names for one town. Surnames are one file-wide map keyed on (FTG surname, ancestry)."""

    def __init__(self, profile, seed):
        self.profile, self.seed = profile, seed
        self.region = profile["names"]
        self.by_ancestry = profile["ancestry_names"]
        self.surnames = {}

    def given(self, person_id, gender, ancestry):
        pool = (self.by_ancestry.get(ancestry) or {}).get("given")
        if not pool:
            pool = self.region[gender] if gender in ("male", "female") else self.region["male"] + self.region["female"]
        return rng_for(self.seed, "given", person_id).choice(pool)

    def surname(self, original, ancestry):
        if not original:
            return original
        key = (original, ancestry)
        if key not in self.surnames:
            self.surnames[key] = self._draw_surname(original, ancestry)
        return self.surnames[key]

    def _draw_surname(self, original, ancestry):
        rng = rng_for(self.seed, "surname", original, ancestry)
        mod = self.by_ancestry.get(ancestry) or {}
        if mod.get("single"):
            return ""
        if mod.get("family"):
            return rng.choice(mod["family"])
        form = weighted(rng, self.region["family_forms"])
        if form == "patronymic":
            return rng.choice(self.region["male"]) + rng.choice(self.region["patronymic_suffixes"])
        return rng.choice(self.region["places" if form == "place" else "trades"])

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

    religion = religion_pass(profile, seed, people, hh, anc_of_hh, ppins)
    converted = conversion_pass(profile, buildings, areas, bpins)

    out_people, ancestry_of = [], {}
    for p in people:
        q = dict(p)
        pid = p["id"]
        if pid in ppins:
            q.update(ppins[pid])
        else:
            anc = anc_of_hh[hh[pid]]
            q["race"] = anc
            q["firstName"] = namer.given(pid, p.get("gender"), anc)
            q["lastName"] = namer.surname(p["lastName"], anc)
            q["religion"] = religion[pid]
            informal = namer.informal(pid)
            if informal:
                q["informalByname"] = informal
        ancestry_of[pid] = q["race"]
        out_people.append(q)

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

    problems = check_derived(people, out_people, buildings, out_buildings, ppins)
    report = make_report(profile, seed, out_people, out_buildings, areas, converted, namer, ppins, bpins, problems)

    ddir = derived_dir(root)
    ddir.mkdir(parents=True, exist_ok=True)
    _write_json(ddir / f"{town}.geojson", out_gj)
    _write_json(ddir / f"{town}.gm.json", {"town": town, "seed": seed, "buildings": out_buildings, "people": out_people})
    (ddir / f"{town}.report.txt").write_text(render_report(report), encoding="utf-8")
    return report


def _write_json(path: Path, obj) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# -- checks and report ---------------------------------------------------------------

FROZEN_PERSON_FIELDS = ("id", "age", "gender", "jobTitle", "placeOfWork", "placeOfResidence",
                        "childInFamilies", "parentInFamilies")


def check_derived(src_people, out_people, src_buildings, out_buildings, pinned) -> list:
    """What a draft must not change, and the family-name rule. Returns problem strings."""
    problems = []
    if len(src_people) != len(out_people) or len(src_buildings) != len(out_buildings):
        problems.append("headcount changed")
    for a, b in zip(src_people, out_people):
        for f in FROZEN_PERSON_FIELDS:
            if a.get(f) != b.get(f):
                problems.append(f"person {a['id']}: {f} changed")
    for a, b in zip(src_buildings, out_buildings):
        if a["id"] != b["id"] or a["buildingType"] != b["buildingType"]:
            problems.append(f"building {a['id']}: id or type changed")
    # one FTG surname + one ancestry -> one new surname, so no family splits
    seen = {}
    for a, b in zip(src_people, out_people):
        if a["id"] in pinned:
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
