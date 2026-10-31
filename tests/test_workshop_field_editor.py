"""
Tests for the Map Workshop field editor Save (#336, PR 1): Save sends only the
fields the GM changed. The server removes a key whose value is null, so a form that
sent every field wrote null for anything it could not show and deleted the line.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities" / "world"))
sys.path.insert(0, str(ROOT / "utilities"))

import devserver
import generate_map_workshop as gmw
from locations.map_icons import ICON_NAMES

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")

# What the form showed when the page opened: Fantasy name blank because it equals the
# title, Icon override on "From Type" because the page has none, Type blank because the
# category is not one the select offers.
OPENED = {
    "name": "Achal",
    "fantasy_name": "",
    "type": "route-node",
    "map_icon": "",
    "visibility": "gm_secrets",
}

PAGE = (
    "---\n"
    "title: Achal\n"
    "visibility: gm_secrets\n"
    "last_updated: 2026-10-26\n"
    "fantasy_name: Achal\n"
    "mapmarker: caravanserai\n"
    "type: caravanserai\n"
    "---\n\nProse that must never change.\n"
)


def _diff(base, cur):
    script = gmw._EF_DIFF_JS + f"\nconsole.log(JSON.stringify(_efDiff({json.dumps(base)},{json.dumps(cur)})));"
    out = subprocess.run([NODE, "-e", script], capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


def _fm_lines(text):
    return re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL).group(1).splitlines()


# -- the defect: what the old all-fields payload did to a page ----------------------

def test_a_null_field_removes_the_line_so_untouched_fields_must_not_be_sent():
    old_payload = {"name": "Achal", "fantasy_name": None, "type": "route-node",
                   "mapmarker": None, "visibility": "gm_secrets"}  # the all-fields shape
    after = devserver._set_frontmatter_fields(PAGE, old_payload)
    lost = [ln for ln in _fm_lines(PAGE) if ln not in _fm_lines(after)]
    assert "fantasy_name: Achal" in lost
    assert "mapmarker: caravanserai" in lost
    assert "type: caravanserai" in lost  # rewritten to route-node


def test_a_patch_with_only_the_changed_key_leaves_every_other_line_alone():
    after = devserver._set_frontmatter_fields(PAGE, {"visibility": "public"})
    before_lines, after_lines = _fm_lines(PAGE), _fm_lines(after)
    changed = [(a, b) for a, b in zip(before_lines, after_lines) if a != b]
    assert len(before_lines) == len(after_lines)
    assert all(a.startswith(("visibility:", "last_updated:")) for a, _ in changed)
    assert "fantasy_name: Achal" in after_lines
    assert "mapmarker: caravanserai" in after_lines
    assert "type: caravanserai" in after_lines
    assert after.endswith("Prose that must never change.\n")


# -- the diff: scenarios 1-7 of the issue --------------------------------------------

@needs_node
def test_unchanged_save_sends_nothing():
    assert _diff(OPENED, dict(OPENED)) == {}


@needs_node
def test_changing_only_the_name_sends_only_the_name():
    assert _diff(OPENED, {**OPENED, "name": "Achal Pass"}) == {"name": "Achal Pass"}


@needs_node
def test_clearing_the_fantasy_name_still_removes_the_line():
    opened = {**OPENED, "fantasy_name": "Old Achal"}
    assert _diff(opened, {**opened, "fantasy_name": ""}) == {"fantasy_name": None}


@needs_node
def test_a_type_off_the_list_is_never_sent():
    off_list = {**OPENED, "type": ""}
    assert _diff(off_list, dict(off_list)) == {}
    assert _diff(OPENED, {**OPENED, "type": ""}) == {}  # the placeholder is not a Type


@needs_node
def test_choosing_a_type_for_an_off_list_page_sends_it():
    off_list = {**OPENED, "type": ""}
    assert _diff(off_list, {**off_list, "type": "town"}) == {"type": "town"}


@needs_node
def test_changing_only_the_visibility_sends_only_the_visibility():
    assert _diff(OPENED, {**OPENED, "visibility": "public"}) == {"visibility": "public"}


@needs_node
def test_an_edit_is_compared_with_the_pages_own_opening_values():
    page_b = {"name": "Achatagh", "fantasy_name": "Achatagh Gate", "type": "town",
              "map_icon": "city", "visibility": "public"}
    assert _diff(page_b, {**page_b, "fantasy_name": "The Gate"}) == {"fantasy_name": "The Gate"}


@needs_node
def test_icon_override_values_map_to_what_the_server_expects():
    assert _diff(OPENED, {**OPENED, "map_icon": "city"}) == {"map_icon": "city"}
    assert _diff(OPENED, {**OPENED, "map_icon": "none"}) == {"map_icon": "none"}
    opened = {**OPENED, "map_icon": "city"}
    assert _diff(opened, {**opened, "map_icon": ""}) == {"map_icon": None}  # back to "From Type"
    assert _diff(opened, dict(opened)) == {}


def test_choosing_an_icon_retires_the_older_map_marker_line():
    page = PAGE.replace("mapmarker: caravanserai\n", "mapmarker: caravanserai\nmap_marker: false\n")
    after = devserver._set_frontmatter_fields(page, {"map_icon": "village"})
    lines = _fm_lines(after)
    assert "map_icon: village" in lines
    assert not any(ln.startswith("map_marker:") for ln in lines)
    assert "mapmarker: caravanserai" in lines  # the older category marker is not touched
    assert "type: caravanserai" in lines


def test_going_back_to_from_type_removes_both_icon_lines():
    page = PAGE.replace("type: caravanserai\n", "type: caravanserai\nmap_icon: none\nmap_marker: false\n")
    after = devserver._set_frontmatter_fields(page, {"map_icon": None})
    assert not any(ln.startswith(("map_icon:", "map_marker:")) for ln in _fm_lines(after))
    assert after.endswith("Prose that must never change.\n")


# -- the wiring around the diff -------------------------------------------------------

def test_type_select_has_a_disabled_placeholder_first():
    panel = gmw._build_panel_edit_coords()
    select = re.search(r'<select id="ef-type">\s*(.*?)</select>', panel, re.DOTALL).group(1)
    assert select.lstrip().startswith('<option value="" disabled>(not on the list)</option>')


def test_app_js_saves_only_the_diff_and_keeps_a_baseline():
    js = gmw._build_app_js("https://example.test/style.json", "", "")
    assert gmw._EF_DIFF_JS in js
    for needle in (
        "function _efRead(){",
        "_efBase=_efRead();",
        "fields=_efDiff(_efBase,cur);",
        '_efStatus.textContent="No changes"',
        "function(){if(_efSlug===slug)_efBase=cur;}",
        "if(onOk)onOk();",
        'else _efType.value="";',
    ):
        assert needle in js, needle
    assert "fantasy_name:_efFantasy.value.trim()||null" not in js
    assert "mapmarker:mm===" not in js
    assert "mapmarker" not in js.split("function _efRead(){")[1].split("}")[0]


def test_icon_override_dropdown_lists_the_registered_icons():
    panel = gmw._build_panel_edit_coords()
    select = re.search(r'<select id="ef-icon">\s*(.*?)</select>', panel, re.DOTALL).group(1)
    values = re.findall(r'<option value="([^"]*)"', select)
    assert values[0] == ""                              # "From Type" first, and the default
    assert values[-1] == "none"                         # hides the pin
    assert values[1:-1] == list(ICON_NAMES)
    assert ">From Type<" in select and 'id="ef-icon-note"' in panel


def test_app_js_shows_where_the_icon_comes_from_and_sends_the_override():
    js = gmw._build_app_js("https://example.test/style.json", "", "")
    for needle in (
        "map_icon:_efIcon.value",
        "function _efShowIcon(){",
        '"Icon: "+from+" (from Type)"',
        '"Icon: "+ov+" (override)"',
        "_efType.addEventListener(\"change\",_efShowIcon);",
        "_efIcon.addEventListener(\"change\",_efShowIcon);",
        "_efOpenCat=p.category||\"\";",
    ):
        assert needle in js, needle
    table = json.loads(re.search(r"_efTypeIcons=(\{.*?\});", js).group(1))
    assert table["village"] == "village" and table["poi"] == "poi"
    assert "dungeon" not in table                       # tier None: draws no pin
    assert all(not v.startswith("cat-") for v in table.values())


def test_baseline_moves_only_after_a_successful_save():
    js = gmw._build_app_js("https://example.test/style.json", "", "")
    # Besides its declaration, _efBase is assigned in two places: when a page opens,
    # and inside the onOk callback.
    assignments = re.findall(r"_efBase=[^;]+;", js)
    assert sorted(assignments) == sorted(["_efBase=null;", "_efBase=_efRead();", "_efBase=cur;"])
    # _patchFrontmatter calls onOk from its success branch only, never from the error one.
    body = js[js.index("function _patchFrontmatter("):]
    ok_branch = body[body.index("if(data.ok){"):body.index("}else{")]
    assert "if(onOk)onOk();" in ok_branch
    assert body.count("onOk()") == 1


@needs_node
def test_app_js_still_parses():
    js = gmw._build_app_js("https://example.test/style.json", "", "")
    tmp = ROOT / "tests" / "_tmp_field_editor_app.js"
    try:
        tmp.write_text(js, encoding="utf-8")
        subprocess.run([NODE, "--check", str(tmp)], capture_output=True, text=True, check=True)
    finally:
        tmp.unlink(missing_ok=True)
