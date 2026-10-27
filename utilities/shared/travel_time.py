"""
Travel-time model shared by the Map Workshop (JS), route index (Python) and,
later, per-leg journeys.

One speed table, editable here only. The Workshop embeds it as `var _TT = {...}`
(see `tt_json()`), so the browser presets and the Python route times can't drift.

Model: a travel day is MARCH_HOURS of marching. Hours for a leg are

    hours = km / (km_per_day / MARCH_HOURS * path_factor * slope_factor)

`path_factor` slows travel when the line leaves the road (terrain, straight cut);
`slope_factor` is a speed multiplier from terrain (1.0 = flat). Birds and dragons
ignore the path entirely.
"""

from __future__ import annotations

import json
import math

MARCH_HOURS = 8.0

# km per day, and whether the mode ignores the path (flies).
SPEEDS: dict[str, dict] = {
    "foot":    {"label": "Foot",    "kmpd": 30,  "fly": False},
    "cart":    {"label": "Cart",    "kmpd": 25,  "fly": False},
    "mounted": {"label": "Mounted", "kmpd": 60,  "fly": False},
    "bird":    {"label": "Bird",    "kmpd": 250, "fly": True},
    "dragon":  {"label": "Dragon",  "kmpd": 500, "fly": True},
}

# Multiplier on speed by how the leg is travelled.
PATH_FACTORS: dict[str, float] = {
    "road": 1.00,
    "terrain": 0.80,
    "straight": 0.70,
}

DEFAULT_MODE = "foot"
DEFAULT_PATH = "road"


def _haversine_km(lon1: float, lat1: float, lon2: float, lat2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


def line_length_km(coords: list) -> float:
    """Length of a [[lon, lat], ...] line in km (0.0 for fewer than two points)."""
    return sum(
        _haversine_km(coords[i][0], coords[i][1], coords[i + 1][0], coords[i + 1][1])
        for i in range(len(coords) - 1)
    )


def normalize_mode(mode: str | None) -> str:
    """Known mode, else the default (a missing or unknown `mode` property is foot)."""
    return mode if mode in SPEEDS else DEFAULT_MODE


def segment_hours(km: float, mode: str | None = None, path: str | None = None,
                  slope_factor: float = 1.0) -> float:
    """Marching hours for a leg of `km` by `mode` along `path`.

    Unknown mode/path fall back to the defaults. Fliers ignore `path`.
    """
    spec = SPEEDS[normalize_mode(mode)]
    path_factor = 1.0 if spec["fly"] else PATH_FACTORS.get(path or DEFAULT_PATH, 1.0)
    speed_kmph = spec["kmpd"] / MARCH_HOURS * path_factor * slope_factor
    if speed_kmph <= 0 or km <= 0:
        return 0.0
    return km / speed_kmph


def hours_to_days(hours: float) -> float:
    return hours / MARCH_HOURS


def format_duration(hours: float, approx: bool = False) -> str:
    """'3 days', '1.5 days', '6 h' — days at MARCH_HOURS/day, hours under one day."""
    p = "~" if approx else ""
    if hours <= 0:
        return f"{p}0 days"
    days = hours_to_days(hours)
    if days < 1:
        return f"{p}{hours:.0f} h"
    return f"{p}{days:.1f} days" if days < 10 else f"{p}{days:.0f} days"


def tt_json() -> str:
    """The table as JSON for `var _TT = ...` in generated pages."""
    return json.dumps(
        {"hours": MARCH_HOURS, "speeds": SPEEDS, "path": PATH_FACTORS,
         "defaultMode": DEFAULT_MODE, "defaultPath": DEFAULT_PATH},
        separators=(",", ":"),
    )
