#!/usr/bin/env python3
"""
ONE-SHOT MIGRATION SCRIPT — DELETE AFTER USE.

Reads every weapon .md under world/weapons/ (recursively, skipping _category.md),
extracts the Range value from the body line `- **Range:** <Value>`, and inserts
`range: <Value>` into the YAML frontmatter block.

Usage:
    python migrate_weapon_range.py [--dry-run] [--vault /path/to/vault]
"""
import argparse
import re
from pathlib import Path


def migrate(vault: Path, dry_run: bool) -> None:
    weapons_root = vault / 'world' / 'weapons'
    files = sorted(f for f in weapons_root.rglob('*.md') if f.name != '_category.md')

    total = migrated = already_done = no_range = 0

    for path in files:
        total += 1
        text = path.read_text(encoding='utf-8')

        # Skip if range: already in frontmatter (idempotent)
        parts = text.split('---\n', 2)
        if len(parts) < 3:
            print(f'  SKIP (no frontmatter): {path.relative_to(vault)}')
            no_range += 1
            continue

        fm_block = parts[1]
        if re.search(r'^range:', fm_block, re.MULTILINE):
            already_done += 1
            continue

        # Extract Range from body
        body = parts[2]
        m = re.search(r'\*\*Range:\*\*\s+(.+)', body)
        if not m:
            print(f'  WARNING (no Range found): {path.relative_to(vault)}')
            no_range += 1
            continue

        range_value = m.group(1).strip()
        new_fm = fm_block.rstrip('\n') + f'\nrange: {range_value}\n'
        new_text = f'---\n{new_fm}---\n{body}'

        rel = path.relative_to(vault)
        if dry_run:
            print(f'  DRY-RUN: {rel}  →  range: {range_value}')
        else:
            path.write_text(new_text, encoding='utf-8')
            print(f'  MIGRATED: {rel}  →  range: {range_value}')
        migrated += 1

    print(f'\nDone. total={total} migrated={migrated} already-done={already_done} no-range={no_range}')


def main() -> None:
    parser = argparse.ArgumentParser(description='ONE-SHOT: add range: to weapon frontmatter')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--vault', default=None)
    args = parser.parse_args()

    vault = Path(args.vault) if args.vault else Path(__file__).parent.parent.parent
    migrate(vault, args.dry_run)


if __name__ == '__main__':
    main()
