"""
Tests for the Map Workshop explicit tool modes (#333 step 5, #351).

Scenarios (posted on #351):
  1. Select is the default; arming Place or Route enters it, arming it again leaves it
  2. Esc returns to Select from any mode
  3. Place is one-shot: the map click that sets the point returns to Select
  4. a mode that belongs to a tab ends when the user leaves that tab
  5. the page wires it: the chip, the arm buttons, Esc, and pin clicks go through the mode
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

# Only the pure transition function is run under node; the rest of _WS_MODE_JS touches the DOM.
_PURE = gmw._WS_MODE_JS.split("var _wsMode=")[0]


def _next(cur, ev, tab=None):
    script = _PURE + f"\nconsole.log(JSON.stringify(_wsModeNext({json.dumps(cur)},{json.dumps(ev)},{json.dumps(tab)})));"
    out = subprocess.run([NODE, "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


@needs_node
@pytest.mark.parametrize("cur,ev,expected", [
    ("select", "arm-place", "place"),
    ("select", "arm-route", "route"),
    ("place", "arm-place", "select"),
    ("route", "arm-route", "select"),
    ("place", "arm-route", "route"),
    ("route", "arm-place", "place"),
])
def test_arming_enters_and_toggles(cur, ev, expected):
    assert _next(cur, ev) == expected


@needs_node
@pytest.mark.parametrize("cur", ["select", "place", "route"])
def test_esc_returns_to_select(cur):
    assert _next(cur, "esc") == "select"


@needs_node
@pytest.mark.parametrize("cur", ["place", "route"])
def test_placed_is_one_shot(cur):
    assert _next(cur, "placed") == "select"


@needs_node
@pytest.mark.parametrize("cur,tab,expected", [
    ("place", "inspector", "place"),
    ("place", "reveal", "select"),
    ("route", "plan-route", "route"),
    ("route", "edit-coords", "select"),
    ("select", "reveal", "select"),
])
def test_leaving_the_tab_ends_its_mode(cur, tab, expected):
    assert _next(cur, "tab", tab) == expected


def test_default_mode_is_select():
    assert 'var _wsMode="select";' in gmw._WS_MODE_JS




def test_wiring_in_generator_source():
    src = (ROOT / "utilities" / "world" / "generate_map_workshop.py").read_text()
    assert "+ _WS_MODE_JS" in src
    assert 'id="ws-mode-chip"' in src and 'id="ws-mode-cancel"' in src
    assert 'data-arm="place"' in src and 'data-arm="route"' in src
    # Place is a click (not mouseup, which also fires at the end of a pan) and ends the mode
    assert 'if(_wsMode!=="place")return;' in src and '_wsSetMode("placed")' in src
    assert 'map.on("mouseup"' not in src
    # pins act by mode first; Plan Route no longer adds stops just because its tab is open
    assert 'if(_wsMode==="route"){if(slug)_addToQueue(slug);return;}' in src
    assert 'if(_activeTab==="plan-route"){_addToQueue' not in src
    assert '_wsSetMode("tab",tab)' in src
