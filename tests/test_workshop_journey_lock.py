"""
Tests for the Journeys lock (#373): a locked journey refuses every edit that
changes its stops, legs or name. Static guards on the generator output, plus
the real guard logic run under node.
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities" / "world"))
sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

import generate_map_workshop as gmw

SOURCE = Path(gmw.__file__).read_text(encoding="utf-8")


def _fn(name):
    start = SOURCE.index(f"function {name}(")
    depth, i, seen = 0, SOURCE.index("{", start), False
    while True:
        c = SOURCE[i]
        depth += c == "{"
        depth -= c == "}"
        if depth == 0:
            return SOURCE[start:i + 1]
        i += 1


GUARDED = ["_ttSetPt", "_ttRemoveStop", "_ttSetMode", "_ttSetPath"]


@pytest.mark.parametrize("name", GUARDED)
def test_every_stop_leg_edit_entry_point_checks_the_lock(name):
    assert "_ttGuard()" in _fn(name)


def test_delete_of_the_loaded_journey_checks_the_lock():
    assert "id===_ttJid&&_ttGuard()" in _fn("_ttDelete")


def test_presets_and_apply_all_path_check_the_lock():
    assert SOURCE.count('if(_ttGuard())return;\n    var mode=btn.dataset.mode;') == 1
    assert "if(!p||_ttGuard())return;" in SOURCE


def test_saved_journeys_load_locked_unless_the_flag_says_false():
    assert "_ttLocked=p.locked!==false;" in _fn("_ttLoad")


def test_clear_makes_the_next_journey_editable_and_save_relocks():
    assert "_ttLocked=false;" in _fn("_ttClear")
    assert "_ttLocked=true;" in _fn("_ttSave")
    assert "locked:true" in _fn("_ttSave")


def test_markers_follow_the_lock():
    assert "draggable:!_ttLocked" in _fn("_ttAddMarker")
    assert "setDraggable(!_ttLocked)" in _fn("_ttApplyLock")


def test_the_lock_control_exists_and_reports_pressed_state():
    assert 'id="tt-lock-btn"' in gmw._build_panel_travel_time()
    assert "aria-pressed" in _fn("_ttApplyLock")
    assert "tt-lockword" in _fn("_ttRenderState")
    assert "— locked" not in _fn("_ttRenderState")


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_guard_blocks_edits_under_node():
    js = "\n".join(_fn(n) for n in ["_ttGuard", "_ttSetPt", "_ttRemoveStop"])
    prog = f"""
var _ttLocked=true,_ttStops=[{{}},{{}}],said="",_JRN={{maxStops:9}};
function _ttSay(m){{said=m;}}
function _ttAddMarker(){{throw new Error("marker added while locked");}}
function _ttMarkDirty(){{throw new Error("dirtied while locked");}}
{js}
_ttSetPt(1,2,"x");_ttRemoveStop(0);
if(_ttStops.length!==2)throw new Error("stops changed while locked");
if(!/locked/.test(said))throw new Error("no message");
_ttLocked=false;
var threw=false;try{{_ttSetPt(1,2,"x");}}catch(e){{threw=/marker added/.test(e.message);}}
if(!threw)throw new Error("unlocked edit did not proceed");
"""
    r = subprocess.run(["node", "-e", prog], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


def test_lock_control_is_an_icon_button_with_a_label_that_follows_state():
    html = gmw._build_panel_travel_time()
    btn = re.search(r'<button[^>]*id="tt-lock-btn"[^>]*>', html).group(0)
    assert "aria-label=" in btn and "title=" in btn
    body = _fn("_ttApplyLock")
    assert "_TT_ICON_LOCKED" in body and "_TT_ICON_OPEN" in body
    assert '"Unlock journey"' in body and '"Lock journey"' in body
    assert body.count("setAttribute(\"aria-label\"") == 1


def test_clicking_a_journey_line_loads_it_only_when_not_mid_edit():
    src = SOURCE
    assert 'layers:["journeys-hit"]' in src
    assert "(_ttLocked||!_ttStops.length)" in src
    assert "_ttLoad(_jh[0].properties.id)" in src


def test_saved_row_name_is_clickable_and_unlocked_word_is_green():
    assert '.querySelector(".tt-saved-name").addEventListener("click"' in SOURCE
    assert ".tt-lockword.open" in SOURCE


def test_other_work_displaces_the_loaded_journey():
    """A clean journey unloads; unsaved changes ask first and Cancel drops the action."""
    body = SOURCE.split("function _ttStepAside(){")[1].split("}\n")[0]
    assert 'if(_ttDirty&&!confirm("Discard unsaved journey changes?"))return false;' in body
    assert "_ttClear();return true;" in body
    assert "function _ttRelock(){" in SOURCE
    relock = SOURCE.split("function _ttRelock(){")[1].split("}\n")[0]
    assert "fetch" not in relock  # local only, never PATCHed
    assert "'if(!_ttStepAside())return false;'\n        '_selectedRouteId=" in SOURCE
    assert "'if(!_ttStepAside())return;'\n        '_openFieldEditor(feature);'" in SOURCE
    assert 'if(nxt==="place"&&typeof _ttStepAside==="function"&&!_ttStepAside())return;' in SOURCE
    assert 'if(tab!=="travel-time"&&typeof _ttRelock==="function")_ttRelock();' in SOURCE


def test_journey_line_click_works_from_any_tab_and_pins_routes_win():
    assert '_setTab("travel-time");}' in SOURCE
    assert "_onPin" in SOURCE and "_onRt" in SOURCE
    assert 'else if(_activeTab==="travel-time"&&!_onPin)_ttSetPt(' in SOURCE
    # a locked loaded journey no longer adds stops from a pin click
    assert '_activeTab==="travel-time"&&!(_ttJid&&_ttLocked)' in SOURCE
