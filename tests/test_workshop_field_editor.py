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

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")

# What the form showed when the page opened: Fantasy name blank because it equals the
# title, Map Marker on auto because the file's value is not on the list, Type blank
# because the category is not one the select offers.
OPENED = {
    "name": "Achal",
    "fantasy_name": "",
    "type": "route-node",
    "mapmarker": "",
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
                   "mapmarker": None, "visibility": "gm_secrets"}
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
              "mapmarker": "city", "visibility": "public"}
    assert _diff(page_b, {**page_b, "fantasy_name": "The Gate"}) == {"fantasy_name": "The Gate"}


@needs_node
def test_map_marker_values_map_to_what_the_server_expects():
    assert _diff(OPENED, {**OPENED, "mapmarker": "city"}) == {"mapmarker": "city"}
    assert _diff(OPENED, {**OPENED, "mapmarker": "false"}) == {"mapmarker": False}
    opened = {**OPENED, "mapmarker": "city"}
    assert _diff(opened, {**opened, "mapmarker": ""}) == {"mapmarker": None}


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
