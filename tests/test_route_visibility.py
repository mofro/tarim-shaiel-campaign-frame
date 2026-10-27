"""
Tests for the player-visibility rule for routes (#310).

A route shows to players only if its own visibility is public AND both end
locations are public. Everything else fails closed.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "utilities"))

from shared import route_visibility as rv


def loc(slug, lon, lat, visibility):
    return {"type": "Feature", "id": f"location_{slug}",
            "properties": {"slug": slug, "visibility": visibility},
            "geometry": {"type": "Point", "coordinates": [lon, lat]}}


def route(rid, a, b, visibility="public", mid=None):
    coords = [list(a)] + ([list(mid)] if mid else []) + [list(b)]
    props = {"label": rid}
    if visibility is not None:
        props["visibility"] = visibility
    return {"type": "Feature", "id": rid, "properties": props,
            "geometry": {"type": "LineString", "coordinates": coords}}


def fc(*features):
    return {"type": "FeatureCollection", "features": list(features)}


A = (70.0, 40.0)
B = (71.0, 40.0)
C = (72.0, 40.0)


def ids(gj):
    return [f["id"] for f in gj["features"]]


def test_public_route_between_public_ends_is_visible():
    locs = fc(loc("a", *A, "public"), loc("b", *B, "public"))
    assert ids(rv.visible_routes(fc(route("r1", A, B)), locs)) == ["r1"]


def test_public_route_with_a_hidden_end_is_hidden():
    locs = fc(loc("a", *A, "public"), loc("b", *B, "gm_secrets"))
    assert ids(rv.visible_routes(fc(route("r1", A, B)), locs)) == []
    # either end
    locs = fc(loc("a", *A, "gm_secrets"), loc("b", *B, "public"))
    assert ids(rv.visible_routes(fc(route("r1", A, B)), locs)) == []


def test_gm_only_route_between_public_ends_is_hidden():
    locs = fc(loc("a", *A, "public"), loc("b", *B, "public"))
    assert ids(rv.visible_routes(fc(route("r1", A, B, "gm_secrets")), locs)) == []


def test_missing_route_visibility_fails_closed():
    locs = fc(loc("a", *A, "public"), loc("b", *B, "public"))
    assert ids(rv.visible_routes(fc(route("r1", A, B, None)), locs)) == []


def test_unmatched_end_is_hidden_and_warned(capsys):
    locs = fc(loc("a", *A, "public"))  # nothing near B
    assert ids(rv.visible_routes(fc(route("r1", A, B)), locs)) == []
    assert "r1" in capsys.readouterr().err


def test_match_is_against_all_locations_not_just_public_ones():
    # A hidden town sits at B; a public neighbour sits 2 km away. The route ends at
    # the hidden town and must not be rescued by the public one.
    locs = fc(loc("a", *A, "public"),
              loc("hidden-b", *B, "gm_secrets"),
              loc("public-near-b", B[0] + 0.02, B[1], "public"))
    assert ids(rv.visible_routes(fc(route("r1", A, B)), locs)) == []


def test_nearest_location_within_one_km_wins():
    # The end is 0.3 km from the public town and 0.8 km from the hidden one.
    near = (B[0] + 0.0035, B[1])      # ~0.3 km east
    far = (B[0] - 0.0095, B[1])       # ~0.8 km west
    locs = fc(loc("a", *A, "public"), loc("near", *near, "public"), loc("far", *far, "gm_secrets"))
    assert ids(rv.visible_routes(fc(route("r1", A, B)), locs)) == ["r1"]


def test_endpoint_beyond_one_km_does_not_match():
    off = (B[0] + 0.02, B[1])         # ~1.7 km
    locs = fc(loc("a", *A, "public"), loc("b", *off, "public"))
    assert ids(rv.visible_routes(fc(route("r1", A, B)), locs, warn=False)) == []


def test_only_end_points_matter_not_the_middle():
    locs = fc(loc("a", *A, "public"), loc("b", *C, "public"),
              loc("mid", *B, "gm_secrets"))
    assert ids(rv.visible_routes(fc(route("r1", A, C, mid=B)), locs)) == ["r1"]


def test_input_is_not_mutated_and_other_keys_survive():
    routes = fc(route("r1", A, B))
    routes["name"] = "routes"
    locs = fc(loc("a", *A, "gm_secrets"), loc("b", *B, "public"))
    out = rv.visible_routes(routes, locs)
    assert out["name"] == "routes" and ids(out) == []
    assert ids(routes) == ["r1"]


def test_empty_and_missing_inputs():
    assert rv.visible_routes(None, None)["features"] == []
    assert rv.visible_routes(fc(), fc())["features"] == []


def test_waystations_follow_their_route():
    way = fc(
        {"type": "Feature", "properties": {"route_segment": "r1"},
         "geometry": {"type": "Point", "coordinates": [70.5, 40.0]}},
        {"type": "Feature", "properties": {"route_segment": "r2"},
         "geometry": {"type": "Point", "coordinates": [71.5, 40.0]}},
        {"type": "Feature", "properties": {},
         "geometry": {"type": "Point", "coordinates": [72.5, 40.0]}},
    )
    out = rv.visible_waystations(way, fc(route("r1", A, B)))
    assert [f["properties"]["route_segment"] for f in out["features"]] == ["r1"]
    assert rv.visible_waystations(None, fc()) is None
