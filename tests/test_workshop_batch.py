"""
Tests for the Workshop multi-select and batch bar (#353): Shift/Ctrl/Cmd-click selects
several pins, the batch bar sets their visibility together, and the Reveal tab is gone.
The generated panel and the JS spliced into the app have to agree on element ids.
"""

import inspect
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

import generate_map_workshop as gmw

NODE = shutil.which("node")
needs_node = pytest.mark.skipif(NODE is None, reason="node not installed")


def _ids_in(html: str) -> set:
    return set(re.findall(r'id="([^"]+)"', html))


def _app_js() -> str:
    return gmw._build_app_js("https://example.test/style.json", "", "")


def test_multiselect_js_ids_exist_in_the_batch_panel():
    panel_ids = _ids_in(gmw._build_panel_batch())
    wanted = set(re.findall(r'getElementById\("(ms-[^"]+)"\)', gmw._MULTISELECT_JS))
    assert wanted, "expected _MULTISELECT_JS to look up ms-* elements"
    missing = wanted - panel_ids
    assert not missing, f"ids used by _MULTISELECT_JS but not rendered: {sorted(missing)}"


def test_multiselect_js_is_safe_to_inline():
    assert "</script" not in gmw._MULTISELECT_JS.lower()
    assert '"""' not in gmw._MULTISELECT_JS


def test_batch_bar_sits_inside_the_inspector_panel_and_hides_the_single_form():
    src = inspect.getsource(gmw._build_html)
    inspector = src[src.index('id="panel-inspector"'):src.index('id="panel-plan-route"')]
    assert "panel_batch" in inspector and 'id="insp-single"' in inspector
    assert "body.ms-multi #insp-single { display: none; }" in gmw._CSS


def test_the_reveal_tab_is_retired():
    src = inspect.getsource(gmw._build_html)
    assert 'data-tab="reveal"' not in src and 'id="panel-reveal"' not in src
    assert "rv-badge" not in src
    assert not hasattr(gmw, "_build_panel_reveal") and not hasattr(gmw, "_REVEAL_JS")
    js = _app_js()
    for gone in ("_rvStage", "_rvApply", "_rvToggleFromMap", "_wsRevealStaged", '_activeTab==="reveal"'):
        assert gone not in js, gone


def test_app_js_wires_modifier_click_to_the_selection_and_plain_click_clears_it():
    js = _app_js()
    for needle in (
        "window._wsPinAction=function(feature,ev){",
        "_wsPinAction(e.features[0],e.originalEvent);",
        'if(ev&&(ev.shiftKey||ev.ctrlKey||ev.metaKey)&&_activeTab==="inspector"){_msToggle(slug);return;}',
        "if(_msSel.length)window._msClear();",
        'if(tab!=="inspector"&&window._msClear)window._msClear();',
        'id:"reveal-rings"',
        "_msUpdateRings()",
        "function _patchFrontmatterRaw(",
        "function _syncVisibility(",
        "function _refreshLocSource(",
    ):
        assert needle in js, f"missing from app JS: {needle}"


def test_a_modifier_click_precedes_the_single_inspector_open():
    js = _app_js()
    body = js[js.index("window._wsPinAction=function"):]
    assert body.index("_msToggle(slug)") < body.index("_openFieldEditor(feature)")


def test_esc_clears_the_selection_before_the_inspector_closes():
    assert "||_msSel.length)return;" in gmw._INSPECTOR_WIRE_JS
    assert 'e.key!=="Escape"||e.defaultPrevented||!_msSel.length||_msBusy' in gmw._MULTISELECT_JS


def test_apply_writes_visibility_only_and_rebuilds_once_after_the_loop():
    js = gmw._MULTISELECT_JS
    assert js.count("_patchFrontmatterRaw(slug,{visibility:vis})") == 1
    assert js.count('_msRebuild("workshop")') == 1 and js.count('_msRebuild("locations")') == 1
    apply_body = js[js.index("function _msApply()"):js.index("_msListEl.addEventListener")]
    assert apply_body.index("step(0).then") < apply_body.index('_msRebuild("workshop")')
    assert "function step(i)" in apply_body and "return step(i+1)" in apply_body


def test_selecting_adding_and_clearing_never_issue_a_request():
    js = gmw._MULTISELECT_JS
    for fn in ("function _msToggle(", "function _msInView(", "window._msClear=function"):
        body = js[js.index(fn):]
        body = body[:body.index("\n}\n")]
        assert "fetch(" not in body and "_patchFrontmatterRaw" not in body, fn


def test_loc_list_carries_visibility():
    src = inspect.getsource(gmw.main)
    assert '"visibility": loc["visibility"]' in src


# -- behaviour, run under node with stubs for the page ---------------------------------

HARNESS = r"""
const els = {};
function el(id){
  if(!els[id]) els[id] = {id, dataset:{}, hidden:false, disabled:false, textContent:"", innerHTML:"",
    className:"", handlers:{},
    classList:{set:new Set(), add(c){this.set.add(c);}, remove(c){this.set.delete(c);},
      toggle(c,f){ if(f===undefined) f=!this.set.has(c); f?this.set.add(c):this.set.delete(c); },
      contains(c){return this.set.has(c);}},
    addEventListener(t,f){this.handlers[t]=f;}, closest(){return null;}};
  return els[id];
}
const bodyCls = new Set();
global.document = {getElementById: el,
  body:{classList:{toggle(c,f){f?bodyCls.add(c):bodyCls.delete(c);}}},
  addEventListener(t,f){ (global._docH=global._docH||{})[t]=f; }};
global.window = global;
const calls = [];
global.fetch = function(url, opts){
  calls.push({url, method:(opts&&opts.method)||"GET", body:opts&&opts.body});
  return Promise.resolve({json:()=>Promise.resolve({ok:true})});
};
global._locList = JSON.parse(LOCS);
global._locBySlug = {}; _locList.forEach(l=>{_locBySlug[l.slug]=l;});
global._efSlug = null;
let sources = [];
global.map = {getSource(){return {setData(d){sources.push(d.features.length);}};},
  getBounds(){return {contains(c){return c[0]>=0&&c[0]<=10&&c[1]>=0&&c[1]<=10;}};}};
global._wsFlyTo = function(){};
global._refreshLocSource = function(){};
global._patchFrontmatterRaw = function(slug, fields){
  return fetch("/api/locations/"+slug+"/frontmatter",{method:"PATCH",body:JSON.stringify(fields)})
    .then(r=>r.json()).then(d=>{ if(FAIL.indexOf(slug)!==-1) return {ok:false,error:"boom"};
      _locBySlug[slug].visibility = fields.visibility; return d; });
};
"""


def _run(body: str, locs, fail=()):
    script = (
        f"const LOCS = {json.dumps(json.dumps(locs))}; const FAIL = {json.dumps(list(fail))};\n"
        + HARNESS + gmw._MULTISELECT_JS + "\n(async()=>{\n" + body + "\n})();"
    )
    out = subprocess.run([NODE, "-e", script], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout.strip().splitlines()[-1])


LOCS = [
    {"slug": "a", "label": "A", "visibility": "gm_secrets", "lon": 1, "lat": 1},
    {"slug": "b", "label": "B", "visibility": "gm_secrets", "lon": 2, "lat": 2},
    {"slug": "c", "label": "C", "visibility": "public", "lon": 3, "lat": 3},
    {"slug": "far", "label": "Far", "visibility": "gm_secrets", "lon": 50, "lat": 50},
]


@needs_node
def test_two_selected_shows_the_bar_one_does_not():
    r = _run("""
      _msToggle("a"); const one = bodyCls.has("ms-multi");
      _msToggle("b"); const two = bodyCls.has("ms-multi");
      console.log(JSON.stringify({one, two, sel:_msSel, rings:sources[sources.length-1], calls:calls.length}));
    """, LOCS)
    assert r == {"one": False, "two": True, "sel": ["a", "b"], "rings": 2, "calls": 0}


@needs_node
def test_shift_click_with_a_pin_open_seeds_the_selection_with_that_pin():
    r = _run("""
      _efSlug = "a"; _msToggle("b");
      console.log(JSON.stringify({sel:_msSel}));
    """, LOCS)
    assert r["sel"] == ["a", "b"]


@needs_node
def test_toggling_a_selected_pin_removes_it():
    r = _run("""
      _msToggle("a"); _msToggle("b"); _msToggle("a");
      console.log(JSON.stringify({sel:_msSel, multi:bodyCls.has("ms-multi")}));
    """, LOCS)
    assert r == {"sel": ["b"], "multi": False}


@needs_node
def test_add_gm_only_in_view_adds_only_hidden_pins_inside_the_view():
    r = _run("""
      _msToggle("a"); _msToggle("c");
      el("ms-add-hidden-btn").handlers.click();
      console.log(JSON.stringify({sel:_msSel, calls:calls.length}));
    """, LOCS)
    assert r["sel"] == ["a", "c", "b"]      # b added; c already in; far is outside; a already in
    assert r["calls"] == 0


@needs_node
def test_apply_public_patches_only_the_rows_that_differ_then_rebuilds_once():
    r = _run("""
      _msToggle("a"); _msToggle("b"); _msToggle("c");
      el("ms-public-btn").handlers.click();
      const asked = _msPending.slugs.slice();
      el("ms-confirm-yes").handlers.click();
      await new Promise(r=>setTimeout(r,50));
      console.log(JSON.stringify({asked, calls, status:el("ms-status").textContent, sel:_msSel}));
    """, LOCS)
    assert r["asked"] == ["a", "b"]
    patches = [c for c in r["calls"] if c["method"] == "PATCH"]
    assert [c["url"] for c in patches] == ["/api/locations/a/frontmatter", "/api/locations/b/frontmatter"]
    assert all(json.loads(c["body"]) == {"visibility": "public"} for c in patches)
    assert [c["url"] for c in r["calls"] if c["method"] == "POST"] == \
        ["/api/rebuild/workshop", "/api/rebuild/locations"]
    assert r["status"].startswith("✓ Revealed 2")
    assert r["sel"] == []


@needs_node
def test_apply_gm_only_confirmation_warns_players_lose_the_pins():
    r = _run("""
      _msToggle("a"); _msToggle("c");
      el("ms-gm-btn").handlers.click();
      console.log(JSON.stringify({msg:el("ms-confirm-msg").textContent, slugs:_msPending.slugs, calls:calls.length}));
    """, LOCS)
    assert "lose" in r["msg"] and r["slugs"] == ["c"] and r["calls"] == 0


@needs_node
def test_a_failed_row_stays_selected_and_the_rest_still_apply():
    r = _run("""
      _msToggle("a"); _msToggle("b");
      el("ms-public-btn").handlers.click();
      el("ms-confirm-yes").handlers.click();
      await new Promise(r=>setTimeout(r,50));
      console.log(JSON.stringify({sel:_msSel, err:_msErr, status:el("ms-status").textContent,
        posts:calls.filter(c=>c.method==="POST").length}));
    """, LOCS, fail=["a"])
    assert r["sel"] == ["a"] and r["err"] == {"a": "boom"}
    assert "1 failed" in r["status"] and r["posts"] == 2


@needs_node
def test_cancel_writes_nothing():
    r = _run("""
      _msToggle("a"); _msToggle("b");
      el("ms-public-btn").handlers.click();
      el("ms-confirm-no").handlers.click();
      console.log(JSON.stringify({calls:calls.length, pending:_msPending}));
    """, LOCS)
    assert r == {"calls": 0, "pending": None}


@needs_node
def test_esc_clears_the_selection_without_a_request():
    r = _run("""
      _msToggle("a"); _msToggle("b");
      let prevented = false;
      _docH.keydown({key:"Escape", defaultPrevented:false, preventDefault(){prevented=true;}});
      console.log(JSON.stringify({sel:_msSel, prevented, multi:bodyCls.has("ms-multi"), calls:calls.length}));
    """, LOCS)
    assert r == {"sel": [], "prevented": True, "multi": False, "calls": 0}


@needs_node
def test_app_js_parses(tmp_path):
    out = tmp_path / "app.js"
    out.write_text(_app_js(), encoding="utf-8")
    r = subprocess.run([NODE, "--check", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
