"""
Tests for the Map Workshop shell (#333 step 2, #347).

Static guards on the generator source; the behaviour itself is walked live in
the browser (see the PR).
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities" / "world"))
sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

import generate_map_workshop as gmw

SOURCE = Path(gmw.__file__).read_text(encoding="utf-8")


def test_no_per_panel_width_caps():
    # one width model: the sidebar sets the width, panels fill it
    assert not re.search(r"#panel-[\w-]+[^{]*\{[^}]*max-width", gmw._CSS)


def test_panels_reserve_scrollbar_gutter():
    rule = re.search(r"\.panel\s*\{([^}]*)\}", gmw._CSS).group(1)
    assert "scrollbar-gutter: stable" in rule


def test_route_index_table_is_fixed_layout_and_truncates():
    assert re.search(r"#panel-route-index table\s*\{[^}]*table-layout:\s*fixed", gmw._CSS)
    assert "text-overflow: ellipsis" in gmw._CSS


def test_route_index_rows_carry_full_text_as_title():
    out = gmw._route_index_html([{
        "id": "route_a<b>", "label": 'Say "hi"', "kind": "main", "dist_km": 1.0,
        "is_approx": False, "mode": "foot", "hours": 1.0, "time": "1 h",
        "visibility": "gm_only", "player_visible": False,
    }])
    assert 'title="route_a&lt;b&gt;"' in out
    assert "Say &quot;hi&quot;" in out
    assert "ri-id" not in out


def test_shell_controls_exist():
    for needle in ('id="sb-toggle"', 'id="sb-resizer"', 'id="sb-show"'):
        assert needle in SOURCE, needle
    assert "sb-hidden" in gmw._CSS


def test_sidebar_width_is_a_token_with_a_floor():
    assert re.search(r"--sb-w:\s*\d+px", gmw._CSS)
    assert re.search(r"#sidebar\s*\{[^}]*width:\s*var\(--sb-w\)[^}]*min-width:\s*340px", gmw._CSS)


def test_collapsible_headings_are_opt_in():
    assert SOURCE.count("data-collapsible>") >= 5
    assert "[data-collapsible]" in gmw._CSS


def test_caret_glyphs_are_css_escapes_not_control_characters():
    assert not any(ord(c) < 32 and c not in "\n\t" for c in gmw._CSS)
    assert '"\\25BE\\00a0"' in gmw._CSS


def test_route_index_uses_eye_icons_for_visibility():
    out = gmw._route_index_html([{
        "id": "route_x", "label": "X", "kind": "main", "dist_km": 1.0,
        "is_approx": False, "mode": "foot", "hours": 1.0, "time": "1 h",
        "visibility": "gm_only", "player_visible": False,
    }])
    assert "ri-eye" in out and 'aria-label="GM only"' in out


def test_layers_dock_into_float_when_sidebar_hidden():
    assert 'id="sb-float"' in SOURCE and "_sbDock" in SOURCE
    assert "#app.sb-hidden #sb-float" in gmw._CSS


def test_terrain_explainer_is_an_info_popup():
    assert 'aria-controls="tt-terrain-info"' in SOURCE
    assert 'id="tt-terrain-info" class="info-pop" hidden' in SOURCE
