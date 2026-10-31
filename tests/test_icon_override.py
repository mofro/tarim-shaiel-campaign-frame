"""
The Icon override (#336, PR 4): a page's `map_icon:` picks its pin icon, or hides the
pin, without changing its Type; new pages are created with a `type:` and no marker.

The parser's `map_marker` field is what every surface copies into the `mapMarker`
property, so what the parser makes of a page is what the map draws.
"""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "utilities"))
sys.path.insert(0, str(ROOT / "utilities" / "world"))

from locations import location_parser  # noqa: E402
from locations.categories import CATEGORIES, TYPES, type_icons  # noqa: E402
from locations.map_icons import ICON_NAMES, REGISTERED_ICONS  # noqa: E402
import add_location  # noqa: E402


def parse(tmp_path, extra="", type_="town"):
    page = tmp_path / "achal.md"
    page.write_text(
        f"---\ntitle: Achal\ncontent_type: location\ntype: {type_}\n{extra}---\n\nBody.\n",
        encoding="utf-8")
    return location_parser.parse_location(page)


# -- the field -------------------------------------------------------------------------

def test_a_page_with_no_override_takes_its_types_icon(tmp_path):
    assert parse(tmp_path)["map_marker"] is None


@pytest.mark.parametrize("raw", ["none", "None", "false", "no", "off"])
def test_none_and_the_yaml_booleans_hide_the_pin(tmp_path, raw):
    assert parse(tmp_path, f"map_icon: {raw}\n")["map_marker"] is False


def test_a_registered_name_is_the_override(tmp_path):
    assert parse(tmp_path, "map_icon: village\n")["map_marker"] == "village"


def test_the_sprite_spelling_and_capitals_are_accepted(tmp_path):
    assert parse(tmp_path, "map_icon: cat-water\n")["map_marker"] == "water"
    assert parse(tmp_path, "map_icon: Fortress\n")["map_marker"] == "fortress"


def test_every_registered_icon_is_a_valid_override(tmp_path):
    assert len(ICON_NAMES) == len(REGISTERED_ICONS)
    for name in ICON_NAMES:
        assert parse(tmp_path, f"map_icon: {name}\n")["map_marker"] == name


def test_an_unregistered_name_is_ignored_with_a_warning(tmp_path, capsys):
    assert parse(tmp_path, "map_icon: dragon-lair\n")["map_marker"] is None
    err = capsys.readouterr().err
    assert "WARN: achal has map_icon: 'dragon-lair'" in err
    assert "not a registered icon" in err


def test_a_value_that_is_not_text_is_ignored_with_a_warning(tmp_path, capsys):
    assert parse(tmp_path, "map_icon: true\n")["map_marker"] is None
    assert "WARN: achal has map_icon: True" in capsys.readouterr().err


def test_the_override_never_changes_the_type(tmp_path):
    page = parse(tmp_path, "map_icon: fortress\n")
    assert page["location_type"] == "town" and page["map_marker"] == "fortress"


# -- the older field -------------------------------------------------------------------

def test_the_older_map_marker_false_still_hides_the_pin(tmp_path):
    assert parse(tmp_path, "map_marker: false\n")["map_marker"] is False


def test_the_older_map_marker_name_still_overrides(tmp_path):
    assert parse(tmp_path, "map_marker: oasis\n")["map_marker"] == "oasis"


def test_map_icon_wins_over_the_older_field(tmp_path):
    assert parse(tmp_path, "map_icon: city\nmap_marker: false\n")["map_marker"] == "city"


def test_a_bad_map_icon_falls_back_to_the_older_field(tmp_path, capsys):
    assert parse(tmp_path, "map_icon: zzz\nmap_marker: oasis\n")["map_marker"] == "oasis"
    assert "map_icon: 'zzz'" in capsys.readouterr().err


# -- creation --------------------------------------------------------------------------

def frontmatter(category):
    return add_location.build_frontmatter(
        "Achal", "achal", 40.5, 65.7, category, "", "A place.", "", "gm_secrets", "2026-10-31")


@pytest.mark.parametrize("category", CATEGORIES)
def test_a_new_page_carries_its_type_and_no_marker_or_type_tag(category):
    text = frontmatter(category)
    lines = text.splitlines()
    assert f"type: {category}" in lines
    assert not any(ln.startswith(("mapmarker:", "map_marker:", "map_icon:")) for ln in lines)
    assert f"- type-{category}" not in lines
    assert "- placeholder" in lines


def test_a_new_page_draws_its_types_pin(tmp_path):
    for t in TYPES:
        if not (t.listed and t.tier):
            continue
        page = tmp_path / "new.md"
        page.write_text(frontmatter(t.slug) + "\n\nBody.\n", encoding="utf-8")
        got = location_parser.parse_location(page)
        assert got is not None and got["map_marker"] is None, t.slug
        assert t.slug in type_icons(), t.slug
