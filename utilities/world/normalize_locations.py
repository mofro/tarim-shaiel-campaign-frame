#!/usr/bin/env python3
"""
Location Frontmatter Normalizer
================================
One-time migration script: ensures all world/locations/*.md files have
consistent frontmatter fields required by the locations HTML generator.

Changes applied per file:
  - Adds `parent_region` (inferred from location coordinates or defaulted to null)
  - Adds `visibility: public` if missing
  - Adds `status: draft` if missing
  - Renames `factions:` → `factions_visible:` (if `factions_visible:` not already present)

Usage:
    python utilities/world/normalize_locations.py --dry-run
    python utilities/world/normalize_locations.py
    python utilities/world/normalize_locations.py --vault /path/to/vault
"""

import re
import sys
import argparse
from pathlib import Path

HERE = Path(__file__).parent
VAULT_ROOT = HERE.parent.parent
LOCATIONS_DIR = VAULT_ROOT / "world" / "locations"

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    raise ImportError(
        "PyYAML is required (pip install -r requirements.txt, or check "
        "you're using the project's intended Python interpreter) — "
        "frontmatter parsing silently degrades to a broken minimal parser "
        "without it, producing empty/incorrect build output."
    )

# ---------------------------------------------------------------------------
# Region inference — rough bounding-box assignment
# Coordinate pairs are (lat, lon); bounds are [lat_min, lon_min, lat_max, lon_max]
# ---------------------------------------------------------------------------

_REGION_BOUNDS = [
    # (region_slug, lat_min, lon_min, lat_max, lon_max)
    # Order matters: first match wins, so more-specific boxes come first.
    ("eastern-terminus",   33.0, 104.0, 36.5, 112.0),
    ("eastern-gateway",    39.0,  93.0, 43.5, 103.5),
    ("tarim-basin",        36.0,  73.0, 43.5,  95.0),  # extended to 43.5 to include Turfan (42.95)
    ("mountain-passes",    36.0,  70.0, 43.0,  80.0),
    ("central-asian-hubs", 36.0,  56.0, 43.0,  73.0),  # extended to lat 36.0 to include Balkh (36.76)
    ("transoxiana",        37.5,  58.0, 43.0,  68.0),
    ("steppe-confederations", 43.0, 60.0, 55.0, 95.0),
]


def _infer_region(lat: float, lon: float) -> str | None:
    """Return the region slug for the given coordinates, or None."""
    for slug, lat_min, lon_min, lat_max, lon_max in _REGION_BOUNDS:
        if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
            return slug
    return None


def _parse_frontmatter_raw(text: str) -> tuple[str, str, str]:
    """Return (before_fm, fm_text, after_fm) — raw string split.

    before_fm includes the opening '---\\n' delimiter.
    after_fm includes the closing '---\\n' delimiter followed by the body.
    Returns ('', '', text) if no frontmatter block found.
    """
    m = re.match(r'^(---\n)(.*?\n)(---\n)', text, re.DOTALL)
    if not m:
        return '', '', text
    # Include closing delimiter in after_fm so the caller's reassembly is:
    #   before_fm + new_fm + after_fm  →  '---\n' + fields + '---\n' + body
    return m.group(1), m.group(2), m.group(3) + text[m.end():]


def _normalize_fm(fm_text: str, source_path: Path, dry_run: bool) -> tuple[str, list[str]]:
    """Apply normalization rules to the raw YAML frontmatter text.

    Returns (updated_fm_text, list_of_changes).
    """
    changes: list[str] = []

    # Load the YAML to inspect values
    if _YAML_AVAILABLE:
        try:
            fm = yaml.safe_load(fm_text) or {}
        except Exception as e:
            return fm_text, [f"  SKIP — YAML parse error: {e}"]
    else:
        # Regex fallback: limited but functional for simple cases
        fm = {}
        for line in fm_text.splitlines():
            kv = line.split(':', 1)
            if len(kv) == 2 and not line.startswith(' '):
                k, v = kv[0].strip(), kv[1].strip()
                fm[k] = v.strip('"\'')

    lines = fm_text.splitlines()
    new_lines = list(lines)
    inserted_after: dict[int, list[str]] = {}

    # --- Rule 1: factions → factions_visible ---
    has_factions = 'factions' in fm
    has_factions_visible = 'factions_visible' in fm
    if has_factions and not has_factions_visible:
        for i, line in enumerate(new_lines):
            if re.match(r'^factions\s*:', line):
                new_lines[i] = 'factions_visible' + line[len('factions'):]
                # Also rename any continuation lines (YAML block list)
                j = i + 1
                while j < len(new_lines) and new_lines[j].startswith('-'):
                    j += 1
                changes.append("  renamed factions → factions_visible")
                break

    # --- Rule 2: visibility ---
    if 'visibility' not in fm:
        # Insert after title if present, else at end
        insert_pos = len(new_lines)
        for i, line in enumerate(new_lines):
            if re.match(r'^title\s*:', line):
                insert_pos = i + 1
                break
        inserted_after.setdefault(insert_pos, []).append('visibility: public')
        changes.append("  added visibility: public")

    # --- Rule 3: status ---
    if 'status' not in fm:
        insert_pos = len(new_lines)
        for i, line in enumerate(new_lines):
            if re.match(r'^(visibility|title)\s*:', line):
                insert_pos = i + 1
                break
        inserted_after.setdefault(insert_pos, []).append('status: draft')
        changes.append("  added status: draft")

    # --- Rule 4: parent_region ---
    if 'parent_region' not in fm:
        lat = lon = None
        loc = fm.get('location')
        if isinstance(loc, list) and len(loc) >= 2:
            try:
                lat, lon = float(loc[0]), float(loc[1])
            except (TypeError, ValueError):
                pass
        region = _infer_region(lat, lon) if lat is not None else None
        region_val = region if region else 'null'
        insert_pos = len(new_lines)
        for i, line in enumerate(new_lines):
            if re.match(r'^(domain|project)\s*:', line):
                insert_pos = i + 1
                break
        inserted_after.setdefault(insert_pos, []).append(f'parent_region: {region_val}')
        changes.append(f"  added parent_region: {region_val}")

    if not changes:
        return fm_text, []

    # Rebuild lines with insertions
    result: list[str] = []
    for i, line in enumerate(new_lines):
        result.append(line)
        if i + 1 in inserted_after:
            result.extend(inserted_after[i + 1])

    # Handle insertions at position 0 (before first line)
    if 0 in inserted_after:
        result = inserted_after[0] + result

    return '\n'.join(result) + '\n', changes


def normalize_file(path: Path, dry_run: bool) -> bool:
    """Normalize a single location file. Returns True if changes were made."""
    text = path.read_text(encoding='utf-8')
    before, fm_text, after = _parse_frontmatter_raw(text)
    if not fm_text:
        print(f"  {path.name}: no frontmatter — SKIPPED")
        return False

    new_fm, changes = _normalize_fm(fm_text, path, dry_run)
    if not changes:
        return False

    print(f"  {path.name}:")
    for c in changes:
        print(c)

    if not dry_run:
        new_text = before + new_fm + after
        path.write_text(new_text, encoding='utf-8')

    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Normalize world/locations/*.md frontmatter for the HTML generator."
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help="Show changes without writing files"
    )
    parser.add_argument(
        '--vault', default=None,
        help="Vault root path (default: auto-detected from script location)"
    )
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else VAULT_ROOT
    locations_dir = vault / "world" / "locations"

    if not locations_dir.is_dir():
        print(f"ERROR: locations directory not found: {locations_dir}", file=sys.stderr)
        return 1

    files = sorted(locations_dir.glob("*.md"))
    if not files:
        print("No .md files found in world/locations/")
        return 0

    mode = "DRY RUN" if args.dry_run else "WRITING"
    print(f"\nLocation normalizer — {mode}")
    print(f"Processing {len(files)} files in {locations_dir}\n")

    changed = 0
    for f in files:
        if normalize_file(f, args.dry_run):
            changed += 1

    verb = "would change" if args.dry_run else "changed"
    print(f"\nDone — {verb} {changed} of {len(files)} files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
