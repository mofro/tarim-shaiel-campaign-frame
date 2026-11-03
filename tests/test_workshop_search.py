"""
Tests for the Map Workshop search box (#333 step 3, #349).

Scenarios (posted on #349):
  1. a typed `lat, lon` is parsed (comma, semicolon or space; either order when only
     one order is valid) and offered as a "Go to" row
  2. text that is not a coordinate pair is not parsed, so name search is unaffected
  3. picking a result runs the same action as clicking its pin (_wsPick -> _wsPinAction)
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities" / "world"))
sys.path.insert(0, str(ROOT / "utilities"))

import generate_map_workshop as gmw

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")


def _parse(q):
    script = gmw._WS_LATLON_JS + f"\nconsole.log(JSON.stringify(_wsParseLatLon({json.dumps(q)})));"
    out = subprocess.run([NODE, "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


@needs_node
@pytest.mark.parametrize("q,expected", [
    ("39.47, 75.99", {"lat": 39.47, "lon": 75.99}),
    ("39.47 75.99", {"lat": 39.47, "lon": 75.99}),
    ("39.47;75.99", {"lat": 39.47, "lon": 75.99}),
    ("  -33.9,151.2 ", {"lat": -33.9, "lon": 151.2}),
    ("100, 39.47", {"lat": 39.47, "lon": 100}),       # first is out of lat range: swapped
    ("10, 120", {"lat": 10, "lon": 120}),
    ("120, 10", {"lat": 10, "lon": 120}),
    ("45, 50", {"lat": 45, "lon": 50}),               # both fit: lat, lon wins
])
def test_lat_lon_forms_parse(q, expected):
    assert _parse(q) == expected


@needs_node
@pytest.mark.parametrize("q", ["", "kashgar", "39.47", "91, 200", "200, 200", "1,2,3", "12 abc", "Bukhara 2"])
def test_non_coordinates_are_not_parsed(q):
    assert _parse(q) is None


def test_pick_runs_the_pin_action_and_the_row_is_wired():
    src = Path(gmw.__file__).read_text(encoding="utf-8")
    assert "_wsPinAction(e.features[0],e.originalEvent)" in src, "pin click must use the shared action"
    # search code sits outside the map-load scope, so the action must be on window
    assert "window._wsPinAction=function" in src
    assert "_wsPick(_locBySlug[el.dataset.slug])" in src, "result click must select, not only fly"
    assert 'data-ll=' in src and "_wsGoTo(" in src
