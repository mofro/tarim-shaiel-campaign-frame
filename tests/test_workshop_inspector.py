"""Client side of the single location inspector (#352): one form for New and Editing."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities" / "world"))

import generate_map_workshop as gmw

JS = gmw._build_app_js("https://example.test/style.json", "", "")
PANEL = gmw._build_panel_inspector("")


def test_one_inspector_tab_and_no_edit_mode_toggle():
    assert 'id="ef-mode"' in PANEL
    assert "edit-mode" not in JS and "ef-panel" not in JS


def test_category_is_never_shown_to_the_user():
    visible = re.sub(r"<[^>]+>", " ", PANEL)
    assert "Category" not in visible and "Type" in visible


def test_new_locations_default_to_gm_only():
    m = re.search(r'<input type="radio" name="ef-vis" value="gm_secrets" checked>', PANEL)
    assert m
    assert 'value="public" checked' not in PANEL


def test_create_sends_type_under_the_category_wire_name_with_visibility():
    body = JS[JS.index("function _efCreate()"):]
    body = body[:body.index("_efSaveBtn.addEventListener")]
    assert "category:typ" in body and "visibility:" in body
    assert "/api/locations/create" in body


def test_save_merges_only_advanced_diff_and_blocks_non_numbers():
    body = JS[JS.index('_efSaveBtn.addEventListener("click"'):]
    assert "_efAdvDiff()" in body and "_efAdvBad" in body
    assert "fields=_efDiff(_efBase,cur)" in body


def test_advanced_loads_lazily_on_open_and_readonly_is_not_editable():
    assert '_efAdv.addEventListener("toggle",_efAdvLoad)' in JS
    ro = JS[JS.index("Object.keys(d.readonly)"):]
    ro = ro[:ro.index("_efAdvBase=_efAdvValues()")]
    assert "createElement(\"input\")" not in ro and "textarea" not in ro


def test_escape_defers_to_the_mode_handler_and_discard_is_confirmed():
    assert "e.defaultPrevented" in JS
    assert 'confirm("Discard unsaved changes?")' in JS
    assert "e.preventDefault();_wsSetMode(\"esc\")" in JS


def test_create_button_waits_for_name_type_and_point():
    sync = JS[JS.index("function _efSync()"):]
    sync = sync[:sync.index("function _efSetMode")]
    assert "_efLat.value&&_efLon.value&&_efName.value.trim()&&_efType.value" in sync


def test_a_place_click_on_a_pin_does_not_also_select_the_pin():
    assert "window._wsJustPlaced=true;setTimeout(function(){window._wsJustPlaced=false;},0);" in JS
    assert 'if(_wsMode==="place"||window._wsJustPlaced)return;' in JS
