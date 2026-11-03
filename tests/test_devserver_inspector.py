"""
Tests for the location inspector's server side (#352): the Advanced frontmatter
listing, the scalar-only write guard, the round trip, and the gm_secrets default.

The hard constraint is #336: Save must never drop frontmatter the form does not show.
"""

import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities"))

import devserver

BODY = "\n# Qarabulaq\n\nProse that must never change.\n"

PAGE = (
    "---\n"
    "title: Qarabulaq\n"
    "project: TTRPG_Tarim_Shaiel\n"
    "visibility: gm_secrets\n"
    "status: draft\n"
    "last_updated: 2026-10-26\n"
    "# a comment the GM wrote\n"
    "location:\n- 40.786629\n- 77.576866\n"
    "name: Qarabulaq\n"
    "type: caravanserai\n"
    "mapmarker: caravanserai\n"
    "fantasy_name: 'The Spring: Qarabulaq'\n"
    "real_world_name: Kara Bulak\n"
    "elevation: 1800\n"
    "map_label: true\n"
    "revealed: 2026-10-30\n"
    "description: >-\n"
    "  First line of a folded description,\n"
    "  second line.\n"
    "tags:\n- caravanserai\n- spring\n"
    "factions_visible:\n- jade-gate\n- road-wardens\n"
    "etymology:\n  origin: Turkic\n  meaning: black spring\n"
    "defautZoom: 7\n"
    "---\n" + BODY
)


def _fm(text):
    return re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL).group(1)


def _lines(text):
    return _fm(text).splitlines()


def _changed(before, after):
    """Frontmatter lines that differ, ignoring last_updated."""
    skip = lambda ln: ln.startswith("last_updated:")
    b = [ln for ln in _lines(before) if not skip(ln)]
    a = [ln for ln in _lines(after) if not skip(ln)]
    return [ln for ln in a if ln not in b], [ln for ln in b if ln not in a]


def test_editing_one_core_field_changes_only_that_line():
    out = devserver._set_frontmatter_fields(PAGE, {"type": "route-node"})
    added, removed = _changed(PAGE, out)
    assert added == ["type: route-node"]
    assert removed == ["type: caravanserai"]
    assert out.endswith(BODY)
    assert "# a comment the GM wrote" in out


def test_editing_one_advanced_scalar_changes_only_that_line():
    out = devserver._set_frontmatter_fields(PAGE, {"real_world_name": "Qara Bulaq"})
    added, removed = _changed(PAGE, out)
    assert added == ["real_world_name: Qara Bulaq"]
    assert removed == ["real_world_name: Kara Bulak"]


def test_numbers_and_booleans_stay_typed():
    out = devserver._set_frontmatter_fields(PAGE, {"elevation": 2100, "map_label": False})
    d = yaml.safe_load(_fm(out))
    assert d["elevation"] == 2100 and isinstance(d["elevation"], int)
    assert d["map_label"] is False


def test_block_scalar_description_is_replaced_whole_not_half():
    out = devserver._set_frontmatter_fields(PAGE, {"description": "New: one line"})
    d = yaml.safe_load(_fm(out))
    assert d["description"] == "New: one line"
    assert "second line" not in out and "folded description" not in out
    assert d["tags"] == ["caravanserai", "spring"]


def test_multiline_value_survives_as_multiline():
    out = devserver._set_frontmatter_fields(PAGE, {"description": "one\ntwo"})
    assert yaml.safe_load(_fm(out))["description"] == "one\ntwo"


def test_deleting_a_block_scalar_key_removes_its_continuation_lines():
    out = devserver._set_frontmatter_fields(PAGE, {"description": None})
    assert "description" not in yaml.safe_load(_fm(out))
    assert "second line" not in out
    assert yaml.safe_load(_fm(out))["etymology"] == {"origin": "Turkic", "meaning": "black spring"}


def test_untouched_lists_and_nested_values_are_byte_identical():
    out = devserver._set_frontmatter_fields(PAGE, {"real_world_name": "X", "type": "route-node"})
    for block in ("tags:\n- caravanserai\n- spring\n",
                  "factions_visible:\n- jade-gate\n- road-wardens\n",
                  "etymology:\n  origin: Turkic\n  meaning: black spring\n",
                  "location:\n- 40.786629\n- 77.576866\n"):
        assert block in out


def test_listing_splits_editable_scalars_from_read_only_values():
    listing = devserver._frontmatter_listing(PAGE)
    assert listing["scalars"]["real_world_name"] == "Kara Bulak"
    assert listing["scalars"]["elevation"] == 1800
    assert listing["scalars"]["map_label"] is True
    assert listing["scalars"]["revealed"] == "2026-10-30"
    assert listing["scalars"]["defautZoom"] == 7
    assert listing["readonly"]["tags"] == ["caravanserai", "spring"]
    assert listing["readonly"]["etymology"] == {"origin": "Turkic", "meaning": "black spring"}
    assert listing["readonly"]["location"] == [40.786629, 77.576866]


def test_listing_leaves_out_the_core_fields_the_form_already_shows():
    scalars = devserver._frontmatter_listing(PAGE)["scalars"]
    for k in ("name", "title", "fantasy_name", "type", "mapmarker", "map_icon", "visibility"):
        assert k not in scalars


@pytest.mark.parametrize("fields", [
    {"tags": "x"},
    {"location": "1,2"},
    {"etymology": "x"},
    {"factions_visible": "x"},
    {"project": "x"},
    {"last_updated": "2000-01-01"},
    {"bad key": "x"},
    {"new_key": ["a", "b"]},
    {"new_key": {"a": 1}},
])
def test_advanced_guard_rejects_lists_nested_protected_and_malformed(fields):
    assert devserver._advanced_field_error(PAGE, fields)


@pytest.mark.parametrize("fields", [
    {"real_world_name": "x"},
    {"elevation": 3},
    {"map_label": False},
    {"description": None},
    {"brand_new_scalar": "x"},
    {"type": "route-node", "visibility": "public"},
])
def test_advanced_guard_accepts_scalars(fields):
    assert devserver._advanced_field_error(PAGE, fields) is None


def test_create_defaults_to_gm_secrets():
    cmd = devserver._create_location_cmd({"name": "N", "lat": 1, "lon": 2, "category": "poi"})
    assert cmd[cmd.index("--visibility") + 1] == "gm_secrets"


def test_create_honours_an_explicit_visibility():
    cmd = devserver._create_location_cmd(
        {"name": "N", "lat": 1, "lon": 2, "category": "poi", "visibility": "public"})
    assert cmd[cmd.index("--visibility") + 1] == "public"


def test_add_location_cli_defaults_to_gm_secrets():
    src = (ROOT / "utilities" / "world" / "add_location.py").read_text()
    assert re.search(r'"--visibility", default="gm_secrets"', src)
    assert 'prompt("Visibility", default="gm_secrets")' in src


def _location_files():
    return sorted((ROOT / "world" / "locations").rglob("*.md"))


def test_every_real_page_lists_without_error():
    for p in _location_files():
        text = p.read_text(encoding="utf-8")
        if text.startswith("---\n"):
            devserver._frontmatter_listing(text)


def test_rewriting_description_on_every_real_page_preserves_all_other_data():
    """The #336 guard, over the real corpus: patch one scalar, nothing else may move."""
    checked = 0
    for p in _location_files():
        text = p.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL)
        if not m:
            continue
        before = yaml.safe_load(m.group(1)) or {}
        if not isinstance(before.get("description"), str):
            continue
        out = devserver._set_frontmatter_fields(text, {"description": before["description"]})
        after = yaml.safe_load(_fm(out)) or {}
        before.pop("last_updated", None)
        after.pop("last_updated", None)
        assert after == before, p.name
        assert out.endswith(text[m.end():]), p.name
        checked += 1
    assert checked > 150
