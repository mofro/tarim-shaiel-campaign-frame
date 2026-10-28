"""
Tests for the basemap peak / volcano markers (#325): the MapTiler style draws six
triangle-icon layers; only "Peak labels" is wanted, only in the Workshop (behind a
Layers-menu checkbox), and the player map hides all six.
"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities" / "world"))
sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

import generate_map_workshop as gmw
from shared import map_style

SIX = {
    "Peak labels", "Peak labels (US)",
    "Volcano labels", "Volcano labels (US)",
    "Volcano labels active", "Volcano labels active (US)",
}
EMPTY = {"type": "FeatureCollection", "features": []}
# basemap_hide_js emits `[...ids].forEach(function(id){if(map.getLayer(id))...})`
HIDE_CALL = re.compile(r'(\[[^\]]*\])\.forEach\(function\(id\)\{if\(map\.getLayer\(id\)\)')


def _hide_lists(js):
    return [json.loads(m.group(1)) for m in HIDE_CALL.finditer(js)]


def _player_html():
    return gmw._build_player_html(loc_geojson=EMPTY, routes_geojson=EMPTY, maptiler_key="k")


def _workshop_js():
    return gmw._build_app_js("https://example.test/style.json", "", "")


def test_the_six_triangle_layers_are_split_into_peak_and_hidden():
    assert set(map_style.BASEMAP_HIDDEN_LAYERS) | {map_style.BASEMAP_PEAK_LAYER} == SIX
    assert map_style.BASEMAP_PEAK_LAYER not in map_style.BASEMAP_HIDDEN_LAYERS
    assert len(set(map_style.BASEMAP_HIDDEN_LAYERS)) == len(map_style.BASEMAP_HIDDEN_LAYERS)
    assert set(map_style.PLAYER_HIDDEN_LAYERS) == SIX


def test_hide_helper_is_guarded_and_uses_exact_ids():
    js = map_style.basemap_hide_js(["Peak labels (US)"])
    assert _hide_lists(js) == [["Peak labels (US)"]]
    assert 'map.setLayoutProperty(id,"visibility","none")' in js


def test_player_map_hides_all_six_with_no_peak_control():
    html = _player_html()
    assert _hide_lists(html) == [list(map_style.PLAYER_HIDDEN_LAYERS)]
    assert "peak-toggle" not in html and "_wsPeaks" not in html


def test_workshop_hides_five_and_leaves_peak_labels_to_the_checkbox():
    js = _workshop_js()
    assert _hide_lists(js) == [list(map_style.BASEMAP_HIDDEN_LAYERS)]
    assert 'getElementById("peak-toggle")' in js and '"_wsPeaks"' in js
    assert json.dumps(map_style.BASEMAP_PEAK_LAYER) in js


def test_workshop_menu_renders_the_peak_checkbox_the_js_looks_up():
    html = gmw._build_html(EMPTY, EMPTY, EMPTY, [], [], "", "k")
    assert re.search(r'<input type="checkbox" id="peak-toggle" checked>', html)
    # in the Layers dropdown, not elsewhere
    dropdown = html.split('id="layers-dropdown"', 1)[1].split('id="ws-zoom"', 1)[0]
    assert 'id="peak-toggle"' in dropdown


needs_node = pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")


def _run_node(tmp_path, source):
    out = tmp_path / "t.js"
    out.write_text(source, encoding="utf-8")
    return subprocess.run(["node", str(out)], capture_output=True, text=True)


@needs_node
def test_hide_snippet_hides_present_layers_and_ignores_missing_ones(tmp_path):
    present = {"Peak labels", "Volcano labels (US)"}
    snippet = map_style.basemap_hide_js(map_style.PLAYER_HIDDEN_LAYERS)
    r = _run_node(tmp_path, (
        "var calls=[];"
        f"var map={{getLayer:function(id){{return {json.dumps(sorted(present))}.indexOf(id)>=0;}},"
        "setLayoutProperty:function(id,p,v){calls.push([id,p,v]);}};"
        + snippet +
        "console.log(JSON.stringify(calls));"
    ))
    assert r.returncode == 0, r.stderr
    assert sorted(json.loads(r.stdout)) == sorted([[i, "visibility", "none"] for i in present])


@needs_node
def test_player_page_script_parses(tmp_path):
    html = _player_html()
    scripts = re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", html, flags=re.S)
    assert scripts
    for i, body in enumerate(scripts):
        r = _run_node_check(tmp_path, i, body)
        assert r.returncode == 0, f"script {i}: {r.stderr}"


def _run_node_check(tmp_path, i, body):
    out = tmp_path / f"p{i}.js"
    out.write_text(body, encoding="utf-8")
    return subprocess.run(["node", "--check", str(out)], capture_output=True, text=True)
