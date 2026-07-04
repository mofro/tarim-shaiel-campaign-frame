#!/usr/bin/env python3
"""
Offline validator for generated LK export files.

Three layers (see schemas/SOURCE.md for provenance):
  1. Envelope — hand-written schema from real LK exports
  2. Content dialect — hand-written LK-dialect schema (NOT vanilla ADF,
     which rejects real LK output)
  3. Semantic checks — self-consistency hash, non-null presentation,
     player-mode purity (no GM strings)

Usage:
    python utilities/lk-bridge/validate_lk.py roundtrip/gm-export.json
    python utilities/lk-bridge/validate_lk.py roundtrip/player.json --player
"""

import sys
import json
import gzip
import hashlib
import argparse
from pathlib import Path

try:
    import jsonschema
except ImportError:
    sys.exit("jsonschema not installed — pip install jsonschema (see requirements.txt)")

SCHEMA_DIR = Path(__file__).parent / 'schemas'


def load_export(path: Path) -> dict:
    raw = path.read_bytes()
    if raw[:2] == b'\x1f\x8b':
        raw = gzip.decompress(raw)
    return json.loads(raw)


def validate(path: Path, player_mode: bool = False) -> int:
    export = load_export(path)
    errors: list[str] = []
    warnings: list[str] = []

    # ── 1. envelope ──
    env_schema = json.loads((SCHEMA_DIR / 'lk-envelope.schema.json').read_text())
    v = jsonschema.Draft7Validator(env_schema)
    for e in sorted(v.iter_errors(export), key=lambda e: list(e.path)):
        errors.append(f"envelope: {'/'.join(str(p) for p in e.path)}: {e.message[:140]}")

    # ── 2. content dialect ──
    dia_schema = json.loads((SCHEMA_DIR / 'lk-dialect.schema.json').read_text())
    dv = jsonschema.Draft7Validator(dia_schema)
    for r in export.get('resources', []):
        for d in r.get('documents', []):
            content = d.get('content')
            if not content or not content.get('type'):
                continue      # blank docs export as content: {} post-rewrite
            errs = list(dv.iter_errors(content))
            if errs:
                best = jsonschema.exceptions.best_match(errs)
                errors.append(f"dialect: resource {r.get('name', '?')!r}: "
                              f"{'/'.join(str(p) for p in best.path)}: {best.message[:140]}")

    # ── 3. semantic ──
    payload = {k: v for k, v in export.items() if k != 'hash'}
    computed = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if computed != export.get('hash'):
        warnings.append("hash: not our self-consistency hash "
                        "(expected for LK-produced exports; LK ignores it on import)")

    if export.get('resourceCount') != len(export.get('resources', [])):
        errors.append(f"semantic: resourceCount {export.get('resourceCount')} != "
                      f"{len(export.get('resources', []))} actual resources")

    absent_presentation = 0
    for r in export.get('resources', []):
        for d in r.get('documents', []):
            if 'presentation' not in d:
                absent_presentation += 1   # post-rewrite LK omits it on some docs
            elif not isinstance(d['presentation'], dict):
                errors.append(f"semantic: resource {r.get('name', '?')!r} document "
                              f"{d.get('id', '?')} has null presentation "
                              f"(HANGS the LK importer)")
    if absent_presentation:
        warnings.append(f"presentation absent on {absent_presentation} document(s) "
                        f"(normal for LK-produced exports; bridge exports always emit it)")

    # mention integrity: every mention id resolves within the export
    ids = {r['id'] for r in export.get('resources', [])}
    def check_mentions(n, res_name):
        if isinstance(n, dict):
            if n.get('type') == 'mention':
                mid = (n.get('attrs') or {}).get('id', '')
                if mid and mid not in ids:
                    warnings.append(f"mention: {res_name!r} → id {mid} not in export "
                                    f"(OK only if targeting an existing LK resource)")
            for v in n.values():
                check_mentions(v, res_name)
        elif isinstance(n, list):
            for v in n:
                check_mentions(v, res_name)
    for r in export.get('resources', []):
        check_mentions(r.get('documents'), r.get('name', '?'))

    if player_mode:
        text = json.dumps(export, ensure_ascii=False)
        for marker, what in [('block-secret', 'block-secret extension'),
                             ('{gm:', 'Tier 1 GM inline'),
                             ('gm_secrets', 'gm_secrets path')]:
            if marker in text:
                errors.append(f"purity: player export contains {what} ({marker!r})")
        for r in export.get('resources', []):
            if r.get('isHidden'):
                errors.append(f"purity: player export contains hidden resource "
                              f"{r.get('name', '?')!r}")

    # ── report ──
    label = 'PLAYER' if player_mode else 'GM'
    print(f"{path.name} [{label} mode] — resources: {len(export.get('resources', []))}")
    for w in warnings:
        print(f"  ⚠ {w}")
    if errors:
        for e in errors[:40]:
            print(f"  ✗ {e}")
        print(f"FAIL: {len(errors)} error(s)")
        return 1
    print("PASS")
    return 0


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate a generated LK export file")
    ap.add_argument('files', nargs='+')
    ap.add_argument('--player', action='store_true',
                    help="Also enforce player-mode purity (no GM content)")
    args = ap.parse_args()
    rc = 0
    for f in args.files:
        rc |= validate(Path(f), player_mode=args.player)
    sys.exit(rc)


if __name__ == '__main__':
    main()
