"""
Tests for the Map Workshop Reveal tab (#309): the generated panel and the
JS spliced into the app have to agree on element ids, and the app JS has to
carry the pieces the tab depends on.
"""

import inspect
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities" / "world"))
sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

import generate_map_workshop as gmw


def _ids_in(html: str) -> set:
    return set(re.findall(r'id="([^"]+)"', html))


def test_reveal_js_ids_exist_in_panel_or_tab_bar():
    panel_ids = _ids_in(gmw._build_panel_reveal())
    # The badge lives on the tab button, which _build_html renders.
    tab_ids = _ids_in(inspect.getsource(gmw._build_html).replace("\\'", "'"))
    wanted = set(re.findall(r'getElementById\("(rv-[^"]+)"\)', gmw._REVEAL_JS))
    assert wanted, "expected _REVEAL_JS to look up rv-* elements"
    missing = wanted - panel_ids - tab_ids
    assert not missing, f"ids used by _REVEAL_JS but not rendered: {sorted(missing)}"


def test_reveal_js_is_safe_to_inline():
    assert "</script" not in gmw._REVEAL_JS.lower()
    assert '"""' not in gmw._REVEAL_JS


def test_app_js_carries_reveal_wiring():
    js = gmw._build_app_js("https://example.test/style.json", "", "")
    assert gmw._REVEAL_JS in js
    for needle in (
        "function _patchFrontmatterRaw(",
        "function _syncVisibility(",
        "function _refreshLocSource(",
        'id:"reveal-rings"',
        'if(_activeTab==="reveal"){_rvToggleFromMap(slug);return;}',
        "_rvUpdateRings()",
    ):
        assert needle in js, f"missing from app JS: {needle}"


def test_html_has_reveal_tab_and_panel():
    src = inspect.getsource(gmw._build_html)
    assert 'data-tab="reveal"' in src
    assert 'id="panel-reveal"' in src
    assert 'id="rv-badge"' in src


def test_loc_list_carries_visibility():
    src = inspect.getsource(gmw.main)
    assert '"visibility": loc["visibility"]' in src


@pytest.mark.skipif(shutil.which("node") is None, reason="node not installed")
def test_app_js_parses(tmp_path):
    js = gmw._build_app_js("https://example.test/style.json", "", "")
    out = tmp_path / "app.js"
    out.write_text(js, encoding="utf-8")
    r = subprocess.run(["node", "--check", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
