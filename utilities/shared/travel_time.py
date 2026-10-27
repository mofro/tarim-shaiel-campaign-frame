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

# --- Terrain paths (#312) ---------------------------------------------------
# The `terrain` path is a least-cost walk across elevation tiles, run in the
# browser (utilities/world/terrain_path.js). Steps are weighted by a relative
# Tobler hiking factor, so the mode speeds above scale by slope instead of
# mixing in absolute Tobler speeds:
#
#     f(S) = exp(-TOBLER_K * (|S + TOBLER_OFFSET| - TOBLER_OFFSET))      f(0) = 1
#
# S is rise over run along a step. Fastest on a gentle downhill (S = -0.05).
# A step steeper than the mode's MAX_SLOPE is impassable, so a cart routes
# around what a walker would climb. Fliers never use the terrain path.

TOBLER_K = 3.5
TOBLER_OFFSET = 0.05

# Assumptions, not measurements. rise/run above which a step is refused.
MAX_SLOPE: dict[str, float] = {
    "foot":    0.60,
    "mounted": 0.35,
    "cart":    0.12,
}

# AWS Terrain Tiles (terrarium), public CORS, no key. Elevation in metres is
# R*256 + G + B/256 - 32768. Credit: data courtesy of the U.S. Geological Survey
# (SRTM, GMTED2010 and other public-domain sources).
TERRAIN_TILE_URL = "https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"
TERRAIN_MAX_CELLS = 8_000_000   # grid cells a single leg may use
TERRAIN_MIN_ZOOM = 6            # below this the leg is refused
TERRAIN_MAX_ZOOM = 10           # finer than this oversamples the 30-90 m source
TERRAIN_MARGIN_FRAC = 0.15      # search room around the stops, as a share of the leg's span


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


def tobler_factor(slope: float) -> float:
    """Speed multiplier for a step of rise/run `slope` (1.0 on the flat)."""
    return math.exp(-TOBLER_K * (abs(slope + TOBLER_OFFSET) - TOBLER_OFFSET))


def max_slope(mode: str | None) -> float | None:
    """Steepest step `mode` can take on a terrain path; None for fliers."""
    return MAX_SLOPE.get(normalize_mode(mode))


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
         "defaultMode": DEFAULT_MODE, "defaultPath": DEFAULT_PATH,
         "terrain": {"maxSlope": MAX_SLOPE, "toblerK": TOBLER_K, "toblerOffset": TOBLER_OFFSET,
                     "tileUrl": TERRAIN_TILE_URL, "maxCells": TERRAIN_MAX_CELLS,
                     "minZoom": TERRAIN_MIN_ZOOM, "maxZoom": TERRAIN_MAX_ZOOM,
                     "marginFrac": TERRAIN_MARGIN_FRAC}},
        separators=(",", ":"),
    )
