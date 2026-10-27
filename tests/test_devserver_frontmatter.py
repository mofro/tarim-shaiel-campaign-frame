"""
Tests for the devserver's frontmatter writers (#321): saving a value that is
already there must leave the page alone, not append a second copy of the key.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities"))

import devserver

BODY = "\n# Qarabulaq\n\nProse that must never change.\n"

PAGE = (
    "---\n"
    "title: Qarabulaq\n"
    "visibility: gm_secrets\n"
    "last_updated: 2026-10-26\n"
    "location:\n- 40.786629\n- 77.576866\n"
    "name: Qarabulaq\n"
    "type: caravanserai\n"
    "mapmarker: caravanserai\n"
    "---\n" + BODY
)

EDIT = {"name": "Qarabulaq", "type": "route-node", "mapmarker": None, "visibility": "gm_secrets"}


def _fm(text):
    return re.match(r"^---\n(.*?\n)---\n", text, re.DOTALL).group(1)


def _keys(text):
    return re.findall(r"^([A-Za-z_]+):", _fm(text), re.M)


def _location(text):
    m = re.search(r"^location:\n((?:- .*\n)+)", _fm(text), re.M)
    return [ln[2:] for ln in m.group(1).splitlines()]


def _assert_no_duplicate_keys(text):
    keys = _keys(text)
    assert len(keys) == len(set(keys)), f"duplicate keys: {keys}"


def test_saving_the_same_values_repeatedly_adds_no_keys():
    text = devserver._set_frontmatter_fields(PAGE, EDIT)
    for _ in range(3):
        again = devserver._set_frontmatter_fields(text, EDIT)
        assert again == text
        text = again
    _assert_no_duplicate_keys(text)
    assert text.endswith(BODY)


def test_a_changed_value_is_replaced_in_place():
    text = devserver._set_frontmatter_fields(PAGE, {"visibility": "public"})
    _assert_no_duplicate_keys(text)
    assert re.search(r"^visibility: public$", _fm(text), re.M)
    assert _keys(text) == _keys(PAGE)


def test_a_missing_key_is_appended_once():
    text = devserver._set_frontmatter_fields(PAGE, {"fantasy_name": "Kara"})
    again = devserver._set_frontmatter_fields(text, {"fantasy_name": "Kara"})
    assert again == text
    assert _keys(text).count("fantasy_name") == 1


def test_rename_updates_title_and_never_adds_one_when_unchanged():
    renamed = devserver._set_frontmatter_fields(PAGE, {"name": "Karabulak"})
    assert re.search(r"^title: Karabulak$", _fm(renamed), re.M)
    assert _keys(renamed).count("title") == 1
    assert devserver._set_frontmatter_fields(renamed, {"name": "Karabulak"}) == renamed


def test_name_only_page_is_renamed_without_gaining_a_title():
    page = PAGE.replace("title: Qarabulaq\n", "")
    text = devserver._set_frontmatter_fields(page, {"name": "Karabulak"})
    assert "title" not in _keys(text)
    assert re.search(r"^name: Karabulak$", _fm(text), re.M)


def test_page_with_neither_title_nor_name_gets_one_title():
    page = PAGE.replace("title: Qarabulaq\n", "").replace("name: Qarabulaq\n", "")
    text = devserver._set_frontmatter_fields(page, {"name": "Qarabulaq"})
    assert _keys(text).count("title") == 1
    assert devserver._set_frontmatter_fields(text, {"name": "Qarabulaq"}) == text


def test_a_page_already_carrying_duplicates_heals_on_the_next_save():
    doubled = PAGE.replace(
        "mapmarker: caravanserai\n",
        "title: Qarabulaq\ntype: route-node\nvisibility: gm_secrets\n"
        "title: Qarabulaq\ntype: route-node\nvisibility: gm_secrets\n",
    )
    text = devserver._set_frontmatter_fields(doubled, EDIT)
    _assert_no_duplicate_keys(text)
    assert text.endswith(BODY)


def test_clearing_a_field_removes_every_copy():
    doubled = PAGE.replace("---\n" + BODY, "mapmarker: caravanserai\n---\n" + BODY)
    assert _keys(doubled).count("mapmarker") == 2
    text = devserver._set_frontmatter_fields(doubled, {"mapmarker": None})
    assert "mapmarker" not in _keys(text)


def test_saving_the_same_coordinates_keeps_a_two_item_location_list():
    text = devserver._set_location(PAGE, 40.786629, 77.576866)
    assert _location(text) == ["40.786629", "77.576866"]
    assert devserver._set_location(text, 40.786629, 77.576866) == text
    assert text.endswith(BODY)


def test_new_coordinates_replace_the_list():
    text = devserver._set_location(PAGE, 41.5, 78.25)
    assert _location(text) == ["41.5", "78.25"]
    assert _keys(text).count("location") == 1


def test_inline_location_is_converted_once():
    page = PAGE.replace("location:\n- 40.786629\n- 77.576866\n", "location: [40.786629, 77.576866]\n")
    text = devserver._set_location(page, 41.5, 78.25)
    assert _location(text) == ["41.5", "78.25"]
    assert devserver._set_location(text, 41.5, 78.25) == text


def test_missing_location_is_appended_once():
    page = PAGE.replace("location:\n- 40.786629\n- 77.576866\n", "")
    text = devserver._set_location(page, 41.5, 78.25)
    assert _keys(text).count("location") == 1
    assert devserver._set_location(text, 41.5, 78.25) == text


def test_a_doubled_location_list_heals_on_the_next_save():
    page = PAGE.replace(
        "location:\n- 40.786629\n- 77.576866\n",
        "location:\n- 40.786629\n- 77.576866\n- 40.786629\n- 77.576866\n",
    )
    text = devserver._set_location(page, 40.786629, 77.576866)
    assert _location(text) == ["40.786629", "77.576866"]
