"""One Types table decides the pin (#336).

`locations.categories.TYPES` is the single list of location Types. The parser, the
Type dropdowns, the icon expressions, the tier filters and the Display toggles all
read it.

`tests/fixtures/type_pins.json` records, for every Type spelling and on every surface
that draws pins: which tier layer draws it, with which icon, plus each surface's icon
arms and tier membership lists, and what the parser makes of it. PR 2 captured it from
the code as it stood before the table existed, so the table was proved to change
nothing anyone could see. Every later commit that changes a pin regenerates the file,
so its diff is that commit's before-and-after pin list:

    venv/bin/python tests/test_types_table.py
"""

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "utilities"))

GOLDEN = ROOT / "tests" / "fixtures" / "type_pins.json"

# Every spelling worth drawing: each listed Type, the legacy spellings, one unknown
# value, and the empty string (a page with no usable Type is classed "poi" by the
# parser, so the empty probe is only a feature whose category is blank).
PROBES = [
    "city", "capital", "bridge", "landmark", "fortress", "town", "sacred-site", "oasis",
    "lake", "sea", "river", "reservoir", "spring", "well", "caravanserai", "route-node",
    "chokepoint", "mountain-pass", "ruins", "poi", "power-site", "site", "water-body", "Oasis",
    "dungeon", "mythic-landscape", "village", "zz-unknown", "",
]
VISIBILITIES = ("public", "gm_secrets")

# Types on real pages that have no row yet. PR 3 gives each one a row (or `icon: none`)
# and deletes its line here; a value on a page that is in neither place fails.
OFF_TABLE_TYPES = {"mobile entity", "cosmological-realm"}


# ---------------------------------------------------------------------------
# Reading what the generators emit
# ---------------------------------------------------------------------------

_DEC = json.JSONDecoder()


def _decode_at(text, i):
    while text[i] in " \n":
        i += 1
    return _DEC.raw_decode(text, i)


def _ev(x, props):
    """The MapLibre expression subset these layers use, evaluated against one feature."""
    if not isinstance(x, list):
        return x
    op = x[0]
    if op == "get":
        return props.get(x[1])
    if op == "!=":
        return _ev(x[1], props) != _ev(x[2], props)
    if op == "==":
        return _ev(x[1], props) == _ev(x[2], props)
    if op == "all":
        return all(_ev(a, props) for a in x[1:])
    if op == "concat":
        return "".join(str(_ev(a, props)) for a in x[1:])
    if op == "case":
        rest = x[1:]
        for k in range(0, len(rest) - 1, 2):
            if _ev(rest[k], props):
                return _ev(rest[k + 1], props)
        return _ev(rest[-1], props)
    if op == "match":
        v = _ev(x[1], props)
        rest = x[2:]
        for k in range(0, len(rest) - 1, 2):
            labels = rest[k] if isinstance(rest[k], list) else [rest[k]]
            if v in labels:
                return rest[k + 1]
        return rest[-1]
    raise ValueError(f"unhandled expression {op!r}")


def _layers_json(js):
    """Layers from map_style.location_tiers_js(): JSON objects, one shared icon variable."""
    icon_match, _ = _decode_at(js, js.index("var _iconMatch=") + len("var _iconMatch="))
    out = []
    for m in re.finditer(r"map\.addLayer\(", js):
        end = js.index(");\n", m.end())
        layer = json.loads(js[m.end():end].replace('"icon-image":_iconMatch', '"icon-image":"__M__"'))
        icon = layer["layout"]["icon-image"]
        out.append({"id": layer["id"], "filter": layer["filter"],
                    "icon": icon_match if icon == "__M__" else icon})
    return out


def _layers_literal(js, prefix):
    """Layers from the f-string generators: object-literal keys, JSON arrays inside."""
    out = []
    for m in re.finditer(r'map\.addLayer\(\{id:"(' + re.escape(prefix) + r'[a-z-]*)"', js):
        fi = js.index("filter:", m.end()) + len("filter:")
        ii = js.index('"icon-image":', m.end()) + len('"icon-image":')
        out.append({"id": m.group(1), "filter": _decode_at(js, fi)[0], "icon": _decode_at(js, ii)[0]})
    return out


def _surfaces():
    from locations import generate_locations_html as glh
    from locations import location_components as lc
    from shared import map_style

    return {
        "map": _layers_json(map_style.location_tiers_js()),
        "world": _layers_literal(glh._locations_layers_js(), "locations-"),
        "world_gm_build": _layers_literal(glh._locations_layers_js(gm_mode=True), "locations-"),
        "gm_secret": _layers_literal(glh._gm_secrets_layers_js(), "gm-locations-"),
        "mini": _layers_literal(lc._mini_map_tiered_layers_js(), "mm-locations-"),
    }


def _arms(layers):
    """{category: icon} from a surface's icon match, and its default."""
    case = layers[0]["icon"]
    match = case[-1] if case[0] == "case" else case
    return ({match[k]: match[k + 1] for k in range(2, len(match) - 1, 2)}, match[-1])


def _category_list(expr):
    """The category list in a tier filter's `["match", ["get", "category"], cats, true, false]`.

    The world page's GM build wraps the whole filter in a second `all`, so look inside.
    """
    if isinstance(expr, list) and expr[:2] == ["match", ["get", "category"]]:
        return expr[2]
    for part in expr if isinstance(expr, list) else ():
        found = _category_list(part)
        if found is not None:
            return found
    return None


def _tiers(layers):
    return {L["id"]: _category_list(L["filter"]) for L in layers}


def _drawn(layers, props):
    hits = [[L["id"], _ev(L["icon"], props)] for L in layers if _ev(L["filter"], props)]
    assert len(hits) <= 1, f"{props} is drawn by two tiers: {hits}"
    return hits[0] if hits else None


def current_pins():
    from locations.location_parser import _classify_type

    surfaces = _surfaces()
    pins = {"probes": {}, "arms": {}, "tiers": {}}
    for name, layers in surfaces.items():
        arms, default = _arms(layers)
        pins["arms"][name] = {"arms": arms, "default": default}
        pins["tiers"][name] = {k: v for k, v in _tiers(layers).items()}
    for probe in PROBES:
        row = {"parser_type": _classify_type({"type": probe}),
               "parser_mapmarker": _classify_type({"mapmarker": probe})}
        for vis in VISIBILITIES:
            props = {"category": probe, "mapMarker": None, "visibility": vis}
            row[vis] = {name: _drawn(layers, props) for name, layers in surfaces.items()}
        pins["probes"][probe] = row
    # A mapmarker override and a mapmarker of false, on a city.
    for label, marker in (("<mapmarker: town>", "town"), ("<mapmarker: false>", False)):
        props = {"category": "city", "mapMarker": marker, "visibility": "public"}
        pins["probes"][label] = {"public": {n: _drawn(L, props) for n, L in surfaces.items()}}
    return pins


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_pins_are_what_they_were_before_the_table():
    golden = json.loads(GOLDEN.read_text())
    now = current_pins()
    assert now["tiers"] == golden["tiers"], "a tier's category list changed"
    assert now["arms"] == golden["arms"], "a surface's icon arms changed"
    for probe, row in golden["probes"].items():
        assert now["probes"][probe] == row, f"pin changed for Type {probe!r}"
    assert now == golden


def test_the_probe_list_covers_every_row():
    from locations.categories import TYPES

    missing = [t.slug for t in TYPES if t.slug not in PROBES]
    assert not missing, f"add {missing} to PROBES and regenerate the golden file"


def test_dropdown_order():
    from locations.categories import CATEGORIES, VALID_CATEGORIES

    assert CATEGORIES == [
        "city", "capital", "bridge", "landmark", "fortress", "town", "sacred-site", "mythic-landscape", "oasis",
        "lake", "sea", "river", "reservoir", "spring", "well", "caravanserai", "route-node",
        "chokepoint", "mountain-pass", "ruins", "poi", "power-site", "site",
    ]
    assert VALID_CATEGORIES == frozenset(CATEGORIES)


def test_display_toggles_are_unchanged():
    from shared.map_style import LOCATION_TYPE_TOGGLES

    assert LOCATION_TYPE_TOGGLES == [
        ("city", "Cities"), ("capital", "Capitals"), ("bridge", "Bridges"),
        ("landmark", "Landmarks"), ("fortress", "Fortresses"), ("town", "Towns"),
        ("sacred-site", "Sacred Sites"), ("oasis", "Oases"), ("lake", "Lakes"),
        ("route-node", "Route Nodes"), ("poi", "POIs"),
    ]


def test_rows_name_real_tiers_and_icons():
    from locations.categories import MAP_TIERS, PAGE_TIERS, TYPES
    from locations.map_icons import REGISTERED_ICONS

    assert len({t.slug for t in TYPES}) == len(TYPES), "duplicate row"
    for t in TYPES:
        assert t.map_tier in (None, *MAP_TIERS), t
        assert t.page_tier in (None, *PAGE_TIERS), t
        for icon in (t.map_icon, t.page_icon, t.mini_icon):
            assert icon is None or icon in REGISTERED_ICONS, (t.slug, icon)
        if t.map_tier is None:
            assert t.map_icon is None or t.slug in ("Oasis",), t
    # Unlisted rows are legacy spellings: tolerated, never offered.
    assert [t.slug for t in TYPES if not t.listed] == ["water-body", "dungeon", "Oasis"]


def test_tier_and_icon_coverage_checks_are_clean():
    from locations import categories
    from shared import map_style

    assert map_style.check_tier_coverage() == []
    assert categories.check_icon_coverage() == []
    # One registry: the table does not keep a second copy of the icon names.
    assert not hasattr(categories, "REGISTERED_ICONS")


def test_icon_coverage_notices_an_unregistered_icon(monkeypatch):
    from locations import categories

    monkeypatch.setattr(categories, "TYPES", categories.TYPES + (
        categories.Type("zz-test", map_icon="cat-not-drawn"),))
    warnings = categories.check_icon_coverage()
    assert any("cat-not-drawn" in w for w in warnings)


def _page_types():
    """Every page's `type:`, read the way the parser reads it."""
    found = set()
    for f in sorted((ROOT / "world" / "locations").rglob("*.md")):
        if f.name.startswith(("_", "zz")):
            continue
        m = re.match(r"---\n(.*?)\n---", f.read_text(), re.S)
        fm = (yaml.safe_load(m.group(1)) or {}) if m else {}
        raw = fm.get("type")
        if isinstance(raw, str):
            found.add(raw.lower().replace("_", "-").strip())
    return found


def test_every_page_type_is_a_row():
    from locations.categories import TYPES

    rows = {t.slug.lower() for t in TYPES}
    off_table = _page_types() - rows
    assert off_table == OFF_TABLE_TYPES, (
        "Types on pages with no row (add a row, or `icon: none` for a non-place): "
        f"{sorted(off_table - OFF_TABLE_TYPES)}; rows now in the table but still listed "
        f"as exceptions: {sorted(OFF_TABLE_TYPES - off_table)}")


if __name__ == "__main__":
    GOLDEN.parent.mkdir(exist_ok=True)
    GOLDEN.write_text(json.dumps(current_pins(), indent=1, sort_keys=True) + "\n")
    print(f"wrote {GOLDEN.relative_to(ROOT)}")
