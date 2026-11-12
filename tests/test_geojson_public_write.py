"""
Public geojson runs must never overwrite the tracked GM snapshot.

world/data/tarim-shaiel-locations.geojson is the GM-mode snapshot. A public
run holds only the public subset, so writing it would drop GM-only locations
from the working copy. These tests pin that: --public leaves the default
output byte-identical, --gm still writes it, and an explicit --out is honoured.
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "utilities"))

from geojson import generate_geojson as gg
from locations.location_parser import load_all_locations

SENTINEL = b'{"type": "FeatureCollection", "features": [], "sentinel": true}\n'


def _mappable_count(public_only):
    """Locations the generator turns into features (it skips those without coordinates)."""
    locs = load_all_locations(gg.LOCATIONS_DIR, public_only=public_only)
    return sum(1 for l in locs if l["lat"] is not None and l["lon"] is not None)


def _patch_output(monkeypatch, tmp_path):
    """Point the default output at a temp file holding known bytes."""
    tracked = tmp_path / "tarim-shaiel-locations.geojson"
    tracked.write_bytes(SENTINEL)
    monkeypatch.setattr(gg, "OUTPUT_PATH", tracked)
    return tracked


def test_public_run_leaves_tracked_snapshot_untouched(monkeypatch, tmp_path, capsys):
    tracked = _patch_output(monkeypatch, tmp_path)

    monkeypatch.setattr(sys, "argv", ["generate_geojson.py", "--public"])

    assert gg.main() == 0
    assert tracked.read_bytes() == SENTINEL, "public run rewrote the tracked snapshot"
    assert "does not write" in capsys.readouterr().out


def test_gm_run_still_writes_tracked_snapshot(monkeypatch, tmp_path):
    tracked = _patch_output(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["generate_geojson.py", "--gm"])

    assert gg.main() == 0
    assert tracked.read_bytes() != SENTINEL
    data = json.loads(tracked.read_text(encoding="utf-8"))
    assert len(data["features"]) == _mappable_count(public_only=False)


def test_default_run_still_writes_all_features(monkeypatch, tmp_path):
    tracked = _patch_output(monkeypatch, tmp_path)
    monkeypatch.setattr(sys, "argv", ["generate_geojson.py"])

    assert gg.main() == 0
    assert tracked.read_bytes() != SENTINEL


def test_public_run_with_explicit_out_writes_public_subset(monkeypatch, tmp_path):
    tracked = _patch_output(monkeypatch, tmp_path)
    other = tmp_path / "public.geojson"
    monkeypatch.setattr(sys, "argv", ["generate_geojson.py", "--public", "--out", str(other)])

    assert gg.main() == 0
    assert tracked.read_bytes() == SENTINEL
    data = json.loads(other.read_text(encoding="utf-8"))
    assert len(data["features"]) == _mappable_count(public_only=True)
    assert all(f["properties"]["visibility"] == "public" for f in data["features"])
