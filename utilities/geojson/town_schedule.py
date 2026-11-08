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
DEFAULT_SHIFT = (8, 17)
NIGHT_SHIFT = (17, 2)
GUARD_SHIFTS = [(6, 14), (14, 22), (22, 6)]
SCHOOL = (8, 15)


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


def where(person: dict, buildings: dict, social: list[int], day: int, hour: int) -> tuple[int | None, str]:
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
    if 18 <= hour < SLEEP_FROM and social and _h(person["id"], day, hour // 2) % 3 == 0:
        open_social = [b for b in social if is_open(buildings[b], day, hour)]
        if open_social:
            return open_social[_h(person["id"], day, "where") % len(open_social)], "free time"
    return home, "at home"


def snapshot(people: list[dict], buildings: dict, day: int, hour: int) -> dict:
    """{"where": {pid: [building id or None, reason]}, "count": {building id: n}}."""
    social = sorted(b for b, v in buildings.items() if v.get("specificBuildingType") in SOCIAL_TYPES)
    placed, count = {}, {}
    for p in people:
        b, why = where(p, buildings, social, day, hour)
        placed[p["id"]] = [b, why]
        if b is not None:
            count[b] = count.get(b, 0) + 1
    return {"day": day, "hour": hour, "where": placed, "count": count}
