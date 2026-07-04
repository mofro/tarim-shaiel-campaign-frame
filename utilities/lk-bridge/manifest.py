#!/usr/bin/env python3
"""
LK resource-ID manifest tooling.

``build``: capture real LK resource IDs from an LK re-export into
lk_manifest.json, matching by resource name against the provisional entries
written by to_lk.py.

    python utilities/lk-bridge/manifest.py build roundtrip/lk-reexport.json

ID semantics (proven 2026-07-03): LK resource IDs are stable database keys —
they survive application rewrites and renames — but every IMPORT mints new
IDs. The manifest is therefore valid per LK-project generation; the
``generation.exportId`` field is the staleness guard.
"""

import sys
import json
import gzip
import argparse
from pathlib import Path

BRIDGE_DIR = Path(__file__).parent
MANIFEST_PATH = BRIDGE_DIR / 'lk_manifest.json'


def load_export(path: Path) -> dict:
    raw = path.read_bytes()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return json.loads(raw)


def build(export_file: str, manifest_path: Path) -> None:
    export = load_export(Path(export_file))
    if not manifest_path.exists():
        sys.exit(f"No manifest at {manifest_path} — run to_lk.py first "
                 f"(it writes the provisional entries).")
    manifest = json.loads(manifest_path.read_text())

    by_name = {}
    for r in export.get('resources', []):
        by_name.setdefault(r['name'], []).append(r['id'])

    matched, ambiguous, missing = 0, [], []
    for rel, entry in (manifest.get('resources') or {}).items():
        name = entry.get('lkName', '')
        ids = by_name.get(name, [])
        if len(ids) == 1:
            entry['lkId'] = ids[0]
            matched += 1
        elif len(ids) > 1:
            ambiguous.append((rel, name, ids))
        else:
            missing.append((rel, name))

    manifest['generation'] = {
        'exportId': export.get('exportId'),
        'capturedAt': export.get('exportedAt'),
        'note': 'lkId values are real LK database keys for THIS project generation; '
                'a delete+re-import mints new IDs and requires a fresh capture.',
    }
    manifest_path.write_text(json.dumps(manifest, indent=1))

    print(f"Manifest updated: {manifest_path}")
    print(f"  matched: {matched}")
    if ambiguous:
        print(f"  AMBIGUOUS (same name, multiple LK resources) — resolve manually:")
        for rel, name, ids in ambiguous[:10]:
            print(f"    {rel} → {name!r}: {ids}")
    if missing:
        print(f"  missing from export: {len(missing)}")
        for rel, name in missing[:10]:
            print(f"    {rel} → {name!r}")


def main() -> None:
    ap = argparse.ArgumentParser(description="LK manifest tooling")
    sub = ap.add_subparsers(dest='cmd', required=True)
    b = sub.add_parser('build', help="Capture real LK IDs from a re-export")
    b.add_argument('export_file')
    b.add_argument('--manifest', default=str(MANIFEST_PATH))
    args = ap.parse_args()
    if args.cmd == 'build':
        build(args.export_file, Path(args.manifest))


if __name__ == '__main__':
    main()
