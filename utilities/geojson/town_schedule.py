"""
Derived time-of-day placement for the GM town inspector (#399).

FTG runs a scheduled-occupancy simulation, but its export carries only each building's
`openingTimes` (416 of 1830 in Qarshi) and each person's home, work and study place. This
module guesses from those, so where someone is at a given hour is DERIVED, not FTG's own.
It is deterministic: the same town, day and hour always give the same answer.

Days are 1 to 7 (Monday is 1, matching FTG's `closedDays`), hours 0 to 23.
"""

import zlib

NIGHT_JOBS = {"Bartender", "Server", "Prostitute"}
NIGHT_TYPES = {"tavern", "inn", "brothel", "bar"}
# Where locals spend free evenings. A khan is a freight yard and a caravanserai houses travellers, so both are left out (#406).
SOCIAL_TYPES = {"tavern", "inn", "bar", "quiet bar", "upper class tavern", "raucous dive",
                "small inn", "medium inn", "large inn"}
# Houses that never shut have no openingTimes; their staff rotate over the three watches (#406).
ROUND_CLOCK_TYPES = {"small inn", "medium inn", "large inn", "inn", "caravanserai"}
SLEEP_FROM, SLEEP_TO = 22, 6
# Beds taken on an average night, per cent. Travellers are not people in the data; a house is
# rated for the night and the party shops around (#406).
LODGING_BASE = {"caravanserai": 70, "large inn": 75, "medium inn": 65, "small inn": 55, "inn": 60}
LODGING_BANDS = [(95, "full, turning travellers away"), (80, "nearly full"),
                 (50, "rooms to be had"), (0, "plenty of rooms")]
DEFAULT_SHIFT = (8, 17)
NIGHT_SHIFT = (17, 2)
GUARD_SHIFTS = [(6, 14), (14, 22), (22, 6)]
SCHOOL = (8, 15)
ADULT = 16
# Most a house holds of an evening's drinkers; the rest stay in (#406). Types not listed are uncapped.
EVENING_CAP = {"tavern": 70, "upper class tavern": 60, "quiet bar": 45, "raucous dive": 90,
               "bar": 60, "small inn": 45, "medium inn": 70, "large inn": 110, "inn": 60}


def _h(*parts) -> int:
    return zlib.crc32("|".join(str(p) for p in parts).encode())


def in_span(hour: int, start: int, end: int) -> bool:
    """True when `hour` falls in [start, end), where the span may wrap past midnight."""
    if start == end:
        return True
    return start <= hour < end if start < end else hour >= start or hour < end


def is_open(building: dict, day: int, hour: int) -> bool:
    t = building.get("openingTimes")
    if not t:
        return True
    return day not in (t.get("closedDays") or []) and in_span(hour, t["openHour"], t["closeHour"])


def shift_of(person: dict, work: dict | None) -> tuple[int, int]:
    t = (work or {}).get("openingTimes")
    if t:
        return t["openHour"], t["closeHour"]
    job = person.get("jobTitle")
    if job == "Guard" or (work or {}).get("specificBuildingType") in ROUND_CLOCK_TYPES:
        return GUARD_SHIFTS[_h(person["id"], "shift") % 3]
    if job in NIGHT_JOBS or (work or {}).get("specificBuildingType") in NIGHT_TYPES:
        return NIGHT_SHIFT
    return DEFAULT_SHIFT


def where(person: dict, buildings: dict, social: list[int], day: int, hour: int, friends: dict | None = None) -> tuple[int | None, str]:
    """(building id or None for out in the streets, reason)."""
    home, work, study = person.get("placeOfResidence"), person.get("placeOfWork"), person.get("placeOfStudy")
    if study is not None and day <= 5:
        sb = buildings.get(study)
        t = (sb or {}).get("openingTimes")
        # the school keeps its own week when it has one (a Friday rest day, #406)
        if (is_open(sb, day, hour) if t else in_span(hour, *SCHOOL)):
            return study, "studying"
    if work is not None:
        wb = buildings.get(work)
        start, end = shift_of(person, wb)
        # a night shift that wraps past midnight belongs to the day it started on
        started_day = day if hour >= start or start < end else (day - 2) % 7 + 1
        closed = (wb or {}).get("openingTimes", {}).get("closedDays") or []
        if in_span(hour, start, end) and started_day not in closed:
            return work, "working"
    if in_span(hour, SLEEP_FROM, SLEEP_TO):
        return home, "asleep"
    if 18 <= hour < SLEEP_FROM and (person.get("age") or 99) >= ADULT:
        # an evening out is a sixth of the town at a house of drink; as many call on a friend or
        # walk the streets, and the rest stay in (#406)
        roll = _h(person["id"], day, hour // 2) % 6
        if roll == 0 and social:
            open_social = [b for b in social if is_open(buildings[b], day, hour)]
            if open_social:
                return open_social[_h(person["id"], day, "where") % len(open_social)], "free time"
        homes = [h for h in (friends or {}).get(person["id"], []) if h != home]
        if roll == 1 and homes:
            return homes[_h(person["id"], day, "friend") % len(homes)], "visiting friends"
        if roll == 2:
            return None, "out walking"
    return home, "at home"


def lodging(buildings: dict, day: int) -> dict:
    """{building id: {"pct": beds taken that night, "rating": words}} for each inn and caravanserai.
    Same answer for the same night; the daily swing is a hash, not a model of who arrives."""
    out = {}
    for b, v in sorted(buildings.items()):
        base = LODGING_BASE.get(v.get("specificBuildingType"))
        if base is None:
            continue
        pct = max(5, min(100, base + _h(b, day, "beds") % 51 - 25))
        out[b] = {"pct": pct, "rating": next(w for lo, w in LODGING_BANDS if pct >= lo)}
    return out


def snapshot(people: list[dict], buildings: dict, day: int, hour: int) -> dict:
    """{"where": {pid: [building id or None, reason]}, "count": {building id: n}}."""
    social = sorted(b for b, v in buildings.items() if v.get("specificBuildingType") in SOCIAL_TYPES)
    # friends are the people one works with; their homes are where one calls
    homes: dict = {}
    for p in people:
        if p.get("placeOfWork") is not None and p.get("placeOfResidence") is not None:
            homes.setdefault(p["placeOfWork"], []).append(p["placeOfResidence"])
    friends = {p["id"]: sorted(set(homes.get(p["placeOfWork"], []))) for p in people if p.get("placeOfWork") is not None}
    home_of = {p["id"]: p.get("placeOfResidence") for p in people}
    placed, count = {}, {}
    for p in people:
        b, why = where(p, buildings, social, day, hour, friends)
        placed[p["id"]] = [b, why]
    # a house at its cap turns the last to arrive away, by a fixed order so the day is repeatable
    by_venue: dict = {}
    for pid, (b, why) in placed.items():
        if why == "free time":
            by_venue.setdefault(b, []).append(pid)
    for b, ids in by_venue.items():
        cap = EVENING_CAP.get(buildings[b].get("specificBuildingType"))
        if cap is not None and len(ids) > cap:
            for pid in sorted(ids, key=lambda i: _h(i, day, hour, "cap"))[cap:]:
                placed[pid] = [home_of[pid], "at home"]
    for b, _ in placed.values():
        if b is not None:
            count[b] = count.get(b, 0) + 1
    return {"day": day, "hour": hour, "where": placed, "count": count, "lodging": lodging(buildings, day)}
