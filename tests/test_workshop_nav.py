"""
Tests for the Map Workshop nav rail (#333 step 9, #355).

Static guards on the generator output; hover, pin and touch behaviour are
walked live in the browser (see the PR).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities" / "world"))
sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

import generate_map_workshop as gmw

SOURCE = Path(gmw.__file__).read_text(encoding="utf-8")


def _ids():
    return [s[0] for s in gmw._WS_SECTIONS]


def test_one_section_list_drives_tabs_and_rail():
    tabs = re.findall(r'class="tab-btn[^"]*" data-tab="([\w-]+)"', gmw._tab_buttons_html())
    rail = re.findall(r'class="nav-item[^"]*" data-tab="([\w-]+)"', gmw._nav_rail_html())
    assert tabs == rail == _ids()


def test_every_rail_item_has_tooltip_and_aria_label():
    html = gmw._nav_rail_html()
    for sid, label, _ in gmw._WS_SECTIONS:
        item = re.search(rf'<button[^>]*data-tab="{sid}"[^>]*>', html).group(0)
        assert f'title="{label}"' in item and f'aria-label="{label}"' in item
    for bid in ("nav-pin", "nav-to-tabs"):
        item = re.search(rf'<button[^>]*id="{bid}"[^>]*>', html).group(0)
        assert "title=" in item and "aria-label=" in item


def test_icons_are_decorative():
    assert gmw._nav_rail_html().count('aria-hidden="true"') >= len(gmw._WS_SECTIONS)


def test_first_section_is_current_and_edit_badge_mirrored():
    html = gmw._nav_rail_html()
    assert html.count('aria-current="page"') == 1
    assert 'id="edit-badge-rail"' in html
    assert 'id="edit-badge"' in gmw._tab_buttons_html()


def test_rail_overlays_instead_of_shifting_layout():
    css = gmw._CSS
    assert re.search(r"#nav-rail\s*\{[^}]*width:\s*48px", css)
    inner = re.search(r"#nav-rail-inner\s*\{([^}]*)\}", css).group(1)
    assert "position: absolute" in inner
    assert re.search(r"#nav-rail:hover #nav-rail-inner[^{]*\{[^}]*width:\s*176px", css)


def test_modes_persisted_with_safe_defaults():
    assert '"_wsNav"' in SOURCE and '"_wsNavPin"' in SOURCE
    assert '#app.nav-tabs #nav-rail { display: none; }' in gmw._CSS
    assert '#app:not(.nav-tabs) #tab-bar { display: none; }' in gmw._CSS


def test_nav_labels_meet_type_floor():
    rule = re.search(r"\.nav-item\s*\{([^}]*)\}", gmw._CSS).group(1)
    assert "font-size: var(--fs-1)" in rule  # 0.75rem, uppercase label floor


def test_set_tab_updates_both_navs():
    assert '.tab-btn,.nav-item[data-tab]' in SOURCE


def test_pinned_rail_overlays_when_sidebar_is_narrow():
    assert "#app.nav-pinned.nav-narrow #nav-rail { width: 48px; }" in gmw._CSS
    assert 'offsetWidth<440' in SOURCE
