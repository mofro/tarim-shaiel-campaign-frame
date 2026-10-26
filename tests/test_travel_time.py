"""
Tests for the shared travel-time model (#310): one speed table, length and hours.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

from shared import travel_time as tt


def test_speed_table_matches_agreed_values():
    assert {m: s["kmpd"] for m, s in tt.SPEEDS.items()} == {
        "foot": 30, "cart": 25, "mounted": 60, "bird": 250, "dragon": 500,
    }
    assert tt.PATH_FACTORS == {"road": 1.0, "terrain": 0.8, "straight": 0.7}
    assert tt.MARCH_HOURS == 8


@pytest.mark.parametrize("mode,kmpd", [("foot", 30), ("cart", 25), ("mounted", 60),
                                       ("bird", 250), ("dragon", 500)])
def test_one_day_of_km_is_one_march_day(mode, kmpd):
    assert tt.segment_hours(kmpd, mode, "road") == pytest.approx(8.0)


def test_path_factor_slows_walkers_only():
    road = tt.segment_hours(30, "foot", "road")
    assert tt.segment_hours(30, "foot", "terrain") == pytest.approx(road / 0.8)
    assert tt.segment_hours(30, "foot", "straight") == pytest.approx(road / 0.7)
    # Fliers ignore the path.
    assert tt.segment_hours(250, "bird", "straight") == pytest.approx(8.0)
    assert tt.segment_hours(500, "dragon", "terrain") == pytest.approx(8.0)


def test_slope_factor_is_a_speed_multiplier():
    flat = tt.segment_hours(30, "foot", "road")
    assert tt.segment_hours(30, "foot", "road", slope_factor=0.5) == pytest.approx(flat * 2)


def test_unknown_mode_and_path_fall_back():
    assert tt.segment_hours(30, None, None) == pytest.approx(8.0)
    assert tt.segment_hours(30, "teleport", "moonlight") == pytest.approx(8.0)
    assert tt.normalize_mode("cart") == "cart"
    assert tt.normalize_mode("nope") == "foot"


def test_zero_or_negative_length_is_zero_hours():
    assert tt.segment_hours(0, "foot") == 0.0
    assert tt.segment_hours(-5, "foot") == 0.0


def test_line_length_km():
    # One degree of latitude is about 111.2 km.
    assert tt.line_length_km([[0, 0], [0, 1]]) == pytest.approx(111.19, abs=0.1)
    assert tt.line_length_km([[0, 0], [0, 1], [0, 2]]) == pytest.approx(222.39, abs=0.2)
    assert tt.line_length_km([[0, 0]]) == 0.0
    assert tt.line_length_km([]) == 0.0


def test_format_duration():
    assert tt.format_duration(0) == "0 days"
    assert tt.format_duration(4) == "4 h"
    assert tt.format_duration(8) == "1.0 days"
    assert tt.format_duration(12) == "1.5 days"
    assert tt.format_duration(8 * 12) == "12 days"
    assert tt.format_duration(12, approx=True) == "~1.5 days"


def test_tt_json_round_trips_the_table():
    d = json.loads(tt.tt_json())
    assert d["hours"] == tt.MARCH_HOURS
    assert d["speeds"]["mounted"]["kmpd"] == 60
    assert d["speeds"]["bird"]["fly"] is True
    assert d["path"]["terrain"] == 0.8
    assert "</" not in tt.tt_json()
